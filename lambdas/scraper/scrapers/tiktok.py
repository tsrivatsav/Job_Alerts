from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_tiktok(url: str) -> List[Dict[str, str]]:
    """
    Scraper for TikTok Careers (API).
    Parses filters (category, location, recruitment type) from the URL 
    and sends them as JSON lists to the API.
    """
    print(f"[TikTok] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'api.lifeattiktok.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US',
        'Content-Type': 'application/json',
        'Origin': 'https://lifeattiktok.com',
        'Referer': 'https://lifeattiktok.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'website-path': 'tiktok',
    })

    # 1. Parse Filters from Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Helper to parse comma-separated params into lists
    # Example: "CT_1,CT_2" -> ["CT_1", "CT_2"]
    def get_list_param(key):
        val = query_params.get(key, [''])[0]
        if not val:
            return []
        return val.split(',')

    # Extract specific lists expected by the API
    recruitment_ids = get_list_param('recruitment_id_list')
    category_ids = get_list_param('job_category_id_list')
    location_codes = get_list_param('location_code_list')
    subject_ids = get_list_param('subject_id_list')
    
    # Extract Keyword
    # URL uses 'keyword', but sometimes 'q' is used manually
    keyword = query_params.get('keyword', [''])[0] or query_params.get('q', [''])[0]

    # Determine start offset
    start_offset = int(query_params.get('offset', ['0'])[0])

    api_url = "https://api.lifeattiktok.com/api/v1/public/supplier/search/job/posts"
    
    jobs = []
    MAX_PAGES = 50
    PAGE_SIZE = 12
    
    # Loop through pages
    for i in range(MAX_PAGES):
        # Calculate current offset based on start_offset + loop index
        current_offset = start_offset + (i * PAGE_SIZE)
        
        print(f"[TikTok] Fetching page {i+1} (Offset: {current_offset})...")
        
        # 2. Construct Payload
        # We inject the parsed lists directly into the JSON body
        payload = {
            "recruitment_id_list": recruitment_ids if recruitment_ids else ["1"], # Default to "Regular" if missing
            "job_category_id_list": category_ids,
            "subject_id_list": subject_ids,
            "location_code_list": location_codes,
            "keyword": keyword,
            "limit": PAGE_SIZE,
            "offset": current_offset
        }
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[TikTok] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 3. Extract Jobs
            # Structure: data -> data -> job_post_list
            inner_data = data.get('data', {})
            job_list = inner_data.get('job_post_list', [])
            
            if not job_list:
                print(f"[TikTok] No jobs found at offset {current_offset}. Stopping.")
                break
            
            for item in job_list:
                title = item.get('title')
                job_id = item.get('id')
                
                # Construct URL
                full_url = f"https://lifeattiktok.com/search/{job_id}"
                
                # Extract Location
                city_info = item.get('city_info', {})
                location = city_info.get('en_name', 'Not specified')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # Check for end of results
            if len(job_list) < PAGE_SIZE:
                print("[TikTok] Reached end of results.")
                break
                
            time.sleep(1) 
            
        except Exception as e:
            print(f"[TikTok] Request failed: {e}")
            break

    print(f"[TikTok] Total jobs found: {len(jobs)}")
    return jobs

