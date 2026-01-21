from typing import List, Dict, Any
import requests

def scrape_jane_street(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Jane Street careers page using their JSON API.
    URL: https://www.janestreet.com/jobs/main.json
    """
    
    print(f"[Jane Street] Fetching jobs from API...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Jane Street] Request failed: {e}")
        return []
    
    jobs_data = response.json()
    
    jobs = []
    
    for job in jobs_data:
        try:
            job_id = job.get('id', '')
            title = job.get('position', '')
            location = job.get('city', 'Not specified')
            availability = job.get('availability')
            if location != 'NYC' or availability != 'Full-Time: Experienced':
                continue
            
            # Build job URL
            job_url = f"https://www.janestreet.com/join-jane-street/position/{job_id}/"
            
            jobs.append({
                'title': title,
                'url': job_url,
                'location': location
            })
            
        except Exception as e:
            print(f"[Jane Street] Error parsing job: {e}")
            continue
    
    print(f"[Jane Street] Found {len(jobs)} jobs")
    return jobs

