from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_amazon(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Amazon Careers using the JSON API.
    Iterates through 10 pages by modifying the 'offset' parameter.
    """
    print(f"[Amazon] Scraping: {url}")
    
    session = requests.Session()
    
    # Headers based on your network tab
    session.headers.update({
        'Authority': 'amazon.jobs',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://amazon.jobs',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Prepare API Endpoint
    # We switch the path from /en/search to /en/search.json
    parsed_url = urlparse(url)
    api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/en/search.json"
    
    # 2. Parse Query Parameters from input URL
    # parse_qs returns lists like {'offset': ['10']}, we flatten them
    query_params = parse_qs(parsed_url.query)
    params = {k: v[0] for k, v in query_params.items()}
    
    # Ensure result_limit is set (Amazon default is usually 10)
    params['result_limit'] = '10'
    
    # Determine start offset
    start_offset = int(params.get('offset', 0))
    
    all_jobs = []
    PAGES_TO_SCRAPE = 10
    PAGE_SIZE = 10
    
    for i in range(PAGES_TO_SCRAPE):
        current_offset = start_offset + (i * PAGE_SIZE)
        print(f"[Amazon] Fetching page {i+1} (Offset: {current_offset})...")
        
        # Update offset in params
        params['offset'] = str(current_offset)
        
        try:
            response = session.get(api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Amazon] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # Navigate JSON: root -> jobs (list)
            jobs_list = data.get('jobs', [])
            
            if not jobs_list:
                print(f"[Amazon] No jobs found at offset {current_offset}. Stopping.")
                break
            
            for job in jobs_list:
                # Extract fields based on your JSON snippet
                title = job.get('title')
                
                # Path is relative: "/en/jobs/3154759/sr-research-scientist"
                job_path = job.get('job_path')
                full_url = f"https://amazon.jobs{job_path}"
                
                # Location: prefer 'normalized_location', fallback to 'location'
                location = job.get('normalized_location') or job.get('location')
                
                all_jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # Polite sleep to avoid rate limits
            time.sleep(1)
            
        except Exception as e:
            print(f"[Amazon] Request failed: {e}")
            break

    print(f"[Amazon] Total jobs found: {len(all_jobs)}")
    return all_jobs

