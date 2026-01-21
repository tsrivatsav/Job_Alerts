from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_netflix(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Netflix (Explore/Eightfold.ai).
    Uses the API endpoint: /api/apply/v2/jobs
    Iterates by modifying the 'start' parameter.
    """
    print(f"[Netflix] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'explore.jobs.netflix.net',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://explore.jobs.netflix.net',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL for Search Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract query and location from the user provided URL
    search_query = query_params.get('query', [''])[0]
    search_location = query_params.get('location', [''])[0]
    
    # 2. API Configuration
    api_url = "https://explore.jobs.netflix.net/api/apply/v2/jobs"
    
    jobs = []
    start = 0
    num = 10 # Page size
    MAX_PAGES = 10
    page_count = 0
    
    while page_count < MAX_PAGES:
        print(f"[Netflix] Fetching results starting at {start}...")
        
        # 3. Construct Payload Parameters
        # Matches: domain=netflix.com&start=20&num=10&query=...&location=...&sort_by=new
        params = {
            'domain': 'netflix.com',
            'start': start,
            'num': num,
            'query': search_query,
            'location': search_location,
            'sort_by': 'new' 
        }
        
        try:
            response = session.get(api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Netflix] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 4. Extract Jobs
            positions = data.get('positions', [])
            
            if not positions:
                print(f"[Netflix] No jobs found at start {start}. Stopping.")
                break
            
            for pos in positions:
                title = pos.get('name')
                
                # Use canonical URL if available, else build it
                full_url = pos.get('canonicalPositionUrl')
                if not full_url:
                    job_id = pos.get('id')
                    full_url = f"https://explore.jobs.netflix.net/careers/job/{job_id}"
                
                # Locations
                locs = pos.get('locations', [])
                location_str = "; ".join(locs) if locs else pos.get('location')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
            count = len(positions)
            print(f"[Netflix] Found {count} jobs on this page.")
            
            # Pagination Logic
            start += count
            page_count += 1
            
            # If we received fewer items than requested, we are at the end
            if count < num:
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"[Netflix] Request failed: {e}")
            break

    print(f"[Netflix] Total jobs found: {len(jobs)}")
    return jobs

