import boto3
import json
import os
from datetime import datetime
from typing import List, Dict

from scrapers import get_scraper, has_scraper

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

JOBS_TABLE = os.environ.get('JOBS_TABLE', 'job_scraper_jobs')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


def lambda_handler(event, context):
    company_name = event['company_name']
    url = event['url']
    
    print(f"Scraping jobs for {company_name} at {url}")
    
    if not has_scraper(company_name):
        print(f"No scraper implemented for {company_name}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'No scraper for {company_name}'})
        }
    
    try:
        scrape_fn = get_scraper(company_name)
        jobs = scrape_fn(url)
        print(f"Found {len(jobs)} total jobs")
        
        jobs_table = dynamodb.Table(JOBS_TABLE)
        new_jobs = []
        
        for job in jobs:
            response = jobs_table.get_item(Key={'job_url': job['url']})
            
            if 'Item' not in response:
                new_jobs.append(job)
                
                jobs_table.put_item(Item={
                    'job_url': job['url'],
                    'company_name': company_name,
                    'job_title': job['title'],
                    'location': job.get('location', 'Not specified'),
                    'discovered_at': datetime.utcnow().isoformat(),
                    'notified': True
                })
                
                print(f"New job found: {job['title']}")
        
        if new_jobs:
            send_notification(company_name, new_jobs)
            print(f"Sent notification for {len(new_jobs)} new jobs")
        else:
            print("No new jobs found")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'company': company_name,
                'total_jobs': len(jobs),
                'new_jobs': len(new_jobs)
            })
        }
        
    except Exception as e:
        print(f"Error scraping {company_name}: {str(e)}")
        raise

def send_notification(company_name: str, new_jobs: List[Dict[str, str]]) -> None:
    """Sends SNS notification for new job postings."""
    if not SNS_TOPIC_ARN:
        print("Warning: SNS_TOPIC_ARN not configured, skipping notification")
        return

    job_list = "\n".join([
        f"• {job['title']}\n  {job['url']}\n  {job.get('location', 'Not specified')}"
        for job in new_jobs
    ])

    message = f"""
🚨 New Job Postings Found!

Company: {company_name}
New Positions: {len(new_jobs)}

{job_list}

---
Discovered at: {datetime.utcnow().isoformat()} UTC
    """.strip()

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject=f'🆕 {len(new_jobs)} New Job(s) at {company_name}'
    )