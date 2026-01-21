from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote

def scrape_huggingface(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Hugging Face (Workable).
    Uses the Workable V3 API: /api/v3/accounts/huggingface/jobs
    """
    print(f"[Hugging Face] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'apply.workable.com',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://apply.workable.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract keyword query
    search_query = query_params.get('query', [''])[0]
    
    # API Endpoint
    api_url = "https://apply.workable.com/api/v3/accounts/huggingface/jobs"
    
    jobs = []
    
    print(f"[Hugging Face] Fetching jobs...")
        
    # 2. Construct Payload
    # We allow broad searching by defaulting lists to empty
    payload = {
        "query": search_query,
        "department": [],
        "location": [{'country': "United States", 'countryCode': "US"}], 
        "workplace": [],
        "worktype": []
    }
        
    try:
        response = session.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[Hugging Face] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # 3. Extract Results
        results = data.get('results', [])
        total_count = data.get('total', 0)
            
        if not results:
            print(f"[Hugging Face] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            shortcode = item.get('shortcode')
            
            # Construct URL
            # Workable job links typically follow this pattern
            full_url = f"https://apply.workable.com/huggingface/j/{shortcode}/"
            
            # Extract Location
            # The API provides both 'location' (object) and 'locations' (list)
            loc_obj = item.get('location', {})
            city = loc_obj.get('city')
            region = loc_obj.get('region') or loc_obj.get('country')
            
            parts = [p for p in [city, region] if p]
            location_str = ", ".join(parts)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Hugging Face] Request failed: {e}")

    print(f"[Hugging Face] Total jobs found: {len(jobs)}")
    return jobs

