from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote

def scrape_jump(url: str = "https://www.jumptrading.com/careers") -> List[Dict[str, str]]:
    """
    Scraper for Jump Trading (Greenhouse).
    Uses the Greenhouse Board API: https://boards-api.greenhouse.io/v1/boards/jumptrading/jobs
    """
    print(f"[Jump Trading] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'boards-api.greenhouse.io',
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': 'https://www-webflow.jumptrading.com',
        'Referer': 'https://www-webflow.jumptrading.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    search_query = query_params.get('query', [''])[0].lower()
    
    # 2. API Endpoint
    # Greenhouse allows fetching all jobs for a board in one GET request.
    # We add ?content=true if we wanted descriptions, but for listing we don't need it.
    api_url = "https://boards-api.greenhouse.io/v1/boards/jumptrading/jobs"
    
    jobs = []
    print(f"[Jump Trading] Fetching jobs via API...")
        
    try:
        # Note: Greenhouse uses GET, not POST
        response = session.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"[Jump Trading] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # 3. Extract Results
        # Greenhouse returns a dictionary with a "jobs" list
        results = data.get('jobs', [])
            
        if not results:
            print(f"[Jump Trading] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            
            # Python-side filtering
            if search_query and search_query not in title.lower():
                continue
            
            # Extract URL
            # The API returns 'absolute_url' which directs to the public job page
            full_url = item.get('absolute_url')
            
            # Fallback if absolute_url is missing, construct using ID
            if not full_url:
                job_id = item.get('id')
                # Based on the user provided sample: 
                full_url = f"https://www.jumptrading.com/hr/job?gh_jid={job_id}"
            
            # Extract Location
            # Location is an object: "location": { "name": "Chicago" }
            loc_obj = item.get('location', {})
            location_str = loc_obj.get('name', 'Unknown')
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Jump Trading] Request failed: {e}")

    print(f"[Jump Trading] Total jobs found: {len(jobs)}")
    return jobs

