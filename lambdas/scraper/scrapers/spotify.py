from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote

def scrape_spotify(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Spotify using the 'animal/v1/job/search' API.
    Auto-converts URL query params (lists) into the comma-separated format the API expects.
    """
    print(f"[Spotify] Scraping: {url}")
    
    session = requests.Session()
    # Headers exactly as found in your network tab
    session.headers.update({
        'Authority': 'api-dot-new-spotifyjobs-com.nw.r.appspot.com',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.lifeatspotify.com',
        'Referer': 'https://www.lifeatspotify.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL Parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # 2. Format Parameters for API
    # The API expects comma-separated strings for lists.
    # e.g., Input: {'c': ['backend', 'data']} -> API: c="backend,data"
    api_params = {}
    
    for key, values in query_params.items():
        # Join multiple values with commas
        api_params[key] = ",".join(values)

    # 3. API Endpoint
    api_url = "https://api-dot-new-spotifyjobs-com.nw.r.appspot.com/wp-json/animal/v1/job/search"
    
    jobs = []
    
    try:
        print("[Spotify] Fetching jobs from API...")
        response = session.get(api_url, params=api_params, timeout=30)
        
        if response.status_code != 200:
            print(f"[Spotify] API Error {response.status_code}")
            return []
            
        data = response.json()
        
        # 4. Extract Jobs from 'result'
        results = data.get('result', [])
        
        if not results:
            print("[Spotify] No jobs found.")
            return []
            
        for item in results:
            # Title is in 'text'
            title = item.get('text')
            
            # The 'id' in the response corresponds to the URL slug
            # Example ID: "data-scientist-growth-analytics-performance-marketing"
            slug = item.get('id')
            full_url = f"https://www.lifeatspotify.com/jobs/{slug}"
            
            # Locations is a list of objects
            locs = item.get('locations', [])
            loc_names = [l.get('location') for l in locs if l.get('location')]
            location_str = ", ".join(loc_names)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Spotify] Request failed: {e}")

    print(f"[Spotify] Found {len(jobs)} jobs")
    return jobs

