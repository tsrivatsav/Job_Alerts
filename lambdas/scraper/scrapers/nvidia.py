from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs
import time

def scrape_nvidia(url: str) -> List[Dict[str, str]]:
    """
    Scraper for NVIDIA (Workday).
    Pagination: Loops until no new unique jobs are found.
    """
    print(f"[NVIDIA] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US',
        'Content-Type': 'application/json',
        'Origin': 'https://nvidia.wd5.myworkdayjobs.com',
        'Referer': url,
        'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })

    # 1. Construct API URL
    parsed_url = urlparse(url)
    path_parts = [p for p in parsed_url.path.split('/') if p]
    site_name = path_parts[0] if path_parts else "NVIDIAExternalCareerSite"
    api_url = f"https://{parsed_url.netloc}/wday/cxs/nvidia/{site_name}/jobs"

    # 2. Extract Filters
    query_params = parse_qs(parsed_url.query)
    search_text = query_params.get('q', [''])[0]
    
    current_offset = int(query_params.get('offset', ['0'])[0])
    
    applied_facets = {}
    ignored_params = ['q', 'offset', 'limit']
    for k, v in query_params.items():
        if k not in ignored_params:
            applied_facets[k] = v

    jobs = []
    seen_urls = set()
    limit = 20
    max_pages = 50
    pages_fetched = 0
    total_available = None  # Will be set from first page only
    
    while pages_fetched < max_pages:
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
            
            # Capture total from first page only
            if total_available is None:
                total_available = data.get('total', 0)
                print(f"[NVIDIA] Total jobs available: {total_available}")
            
            # Stop if the list is empty
            if not job_postings:
                print("[NVIDIA] No more jobs returned (empty list). Stopping.")
                break
            
            new_jobs_count = 0
            
            for post in job_postings:
                title = post.get('title')
                external_path = post.get('externalPath')
                full_url = f"https://{parsed_url.netloc}/{site_name}{external_path}"
                location = post.get('locationsText')
                
                # Deduplication check
                if full_url in seen_urls:
                    continue
                
                seen_urls.add(full_url)
                new_jobs_count += 1
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            print(f"[NVIDIA] Page returned {len(job_postings)} jobs, {new_jobs_count} new (Total: {len(jobs)}/{total_available})")
            
            # Stop conditions:
            # 1. No new unique jobs found (all duplicates)
            if new_jobs_count == 0:
                print("[NVIDIA] No new unique jobs found. Stopping.")
                break
            
            # 2. Received fewer items than limit (last page)
            if len(job_postings) < limit:
                print(f"[NVIDIA] Reached last page (got {len(job_postings)} items).")
                break
            
            # 3. We've collected all available jobs
            if len(jobs) >= total_available:
                print(f"[NVIDIA] Collected all {total_available} available jobs.")
                break
                
            # Move to next page
            current_offset += limit
            pages_fetched += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[NVIDIA] Request failed: {e}")
            break

    print(f"[NVIDIA] Total jobs scraped: {len(jobs)}")
    return jobs
