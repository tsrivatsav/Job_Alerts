from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_nvidia(url: str) -> List[Dict[str, str]]:
    """
    Scraper for NVIDIA (Workday).
    Pagination: Loops until 'jobPostings' list is empty.
    """
    print(f"[NVIDIA] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://nvidia.wd5.myworkdayjobs.com',
        'Referer': url,
    })

    # 1. Construct API URL
    parsed_url = urlparse(url)
    path_parts = [p for p in parsed_url.path.split('/') if p]
    site_name = path_parts[0] if path_parts else "NVIDIAExternalCareerSite"
    api_url = f"https://{parsed_url.netloc}/wday/cxs/nvidia/{site_name}/jobs"

    # 2. Extract Filters
    query_params = parse_qs(parsed_url.query)
    search_text = query_params.get('q', [''])[0]
    
    # Check if user provided a starting offset in URL, otherwise 0
    current_offset = int(query_params.get('offset', ['0'])[0])
    
    applied_facets = {}
    ignored_params = ['q', 'offset', 'limit']
    for k, v in query_params.items():
        if k not in ignored_params:
            applied_facets[k] = v

    jobs = []
    limit = 20
    
    while True:
        print(f"[NVIDIA] Fetching offset {current_offset}...")
        
        payload = {
            "appliedFacets": applied_facets,
            "limit": limit,
            "offset": current_offset,
            "searchText": search_text
        }
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[NVIDIA] API Error {response.status_code}")
                break
            
            data = response.json()
            job_postings = data.get('jobPostings', [])
            
            # --- PAGINATION LOGIC ---
            # Stop if the list is empty
            if not job_postings:
                print("[NVIDIA] No more jobs returned (empty list). Stopping.")
                break
                
            for post in job_postings:
                title = post.get('title')
                external_path = post.get('externalPath')
                full_url = f"https://{parsed_url.netloc}/{site_name}{external_path}"
                location = post.get('locationsText')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # If we received fewer items than the limit (e.g., asked for 20, got 5),
            # we know this is the last page.
            if len(job_postings) < limit:
                print(f"[NVIDIA] Reached last page (got {len(job_postings)} items).")
                break
                
            # Move to next page
            current_offset += limit
            time.sleep(1)
            
        except Exception as e:
            print(f"[NVIDIA] Request failed: {e}")
            break

    print(f"[NVIDIA] Total jobs scraped: {len(jobs)}")
    return jobs

