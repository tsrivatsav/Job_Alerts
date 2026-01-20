import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

COMPANIES_TABLE = os.environ.get('COMPANIES_TABLE', 'job_scraper_companies')
SCRAPER_FUNCTION = os.environ.get('SCRAPER_FUNCTION', 'job-scraper-function')

def lambda_handler(event, context):
    """
    Orchestrator Lambda: Reads companies from DynamoDB and triggers scraper for each.
    """
    print("Starting orchestrator...")
    
    companies_table = dynamodb.Table(COMPANIES_TABLE)
    
    # Scan for companies where check == 'Yes'
    response = companies_table.scan(
        FilterExpression='#check = :yes',
        ExpressionAttributeNames={'#check': 'check'},
        ExpressionAttributeValues={':yes': 'Yes'}
    )
    
    companies = response['Items']
    
    # Handle pagination for large tables
    while 'LastEvaluatedKey' in response:
        response = companies_table.scan(
            FilterExpression='#check = :yes',
            ExpressionAttributeNames={'#check': 'check'},
            ExpressionAttributeValues={':yes': 'Yes'},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        companies.extend(response['Items'])
    
    print(f"Found {len(companies)} companies to scrape")
    
    # Invoke scraper for each company
    invoked = 0
    for company in companies:
        try:
            payload = {
                'company_name': company['company_name'],
                'url': company['url']
            }
            
            lambda_client.invoke(
                FunctionName=SCRAPER_FUNCTION,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            
            print(f"Triggered scraper for: {company['company_name']}")
            invoked += 1
            
        except Exception as e:
            print(f"Error invoking scraper for {company['company_name']}: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Triggered scraping for {invoked} companies',
            'companies': [c['company_name'] for c in companies]
        })
    }