from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_uber(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Uber Careers.
    Parses URL parameters to construct the complex JSON payload required by the API.
    """
    print(f"[Uber] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'www.uber.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://www.uber.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-csrf-token': 'x', # As seen in your headers
    })

    # 1. Parse Input URL Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract Keyword
    search_query = query_params.get('query', [''])[0]
    
    # Extract Simple Lists (Department, Team)
    departments = query_params.get('department', [])
    teams = query_params.get('team', [])
    
    # Extract & Structure Locations
    # URL format: location=USA-California-San Francisco
    # API format: {"country": "USA", "region": "California", "city": "San Francisco"}
    raw_locations = query_params.get('location', [])
    structured_locations = []
    
    for loc in raw_locations:
        parts = loc.split('-')
        # Simple heuristic based on your example: Country-Region-City
        if len(parts) >= 3:
            structured_locations.append({
                "country": parts[0],
                "region": parts[1],
                "city": parts[2]
            })
        elif len(parts) == 1:
            # Fallback for just Country
            structured_locations.append({"country": parts[0]})

    api_url = "https://www.uber.com/api/loadSearchJobsResults?localeCode=en"
    
    jobs = []
    page = 0
    limit = 10
    MAX_PAGES = 10
    
    # Loop through pages (Uber API uses 0-based page index, limit 10)
    while page < MAX_PAGES:
        print(f"[Uber] Fetching page {page}...")
        
        # 2. Construct JSON Payload
        payload = {
            "limit": limit,
            "page": page,
            "params": {
                "query": search_query,
                "department": departments,
                "team": teams,
                "location": structured_locations
            }
        }
        
        # Remove empty keys to keep payload clean
        if not departments: del payload['params']['department']
        if not teams: del payload['params']['team']
        if not structured_locations: del payload['params']['location']
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[Uber] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 3. Extract Jobs
            # Structure: data -> results (list)
            # Note: The root object has "status": "success", "data": { "results": [...] }
            results = data.get('data', {}).get('results', [])
            
            if not results:
                print(f"[Uber] No jobs found on page {page}. Stopping.")
                break
            
            for item in results:
                title = item.get('title')
                job_id = item.get('id')
                
                # Construct URL
                # Uber URLs are usually /global/en/careers/list/{id}/
                full_url = f"https://www.uber.com/global/en/careers/list/{job_id}/"
                
                # Location Extraction
                # "allLocations": [{"city": "Sunnyvale", "region": "California", "country": "USA"}]
                all_locs = item.get('allLocations', [])
                loc_strings = []
                for loc in all_locs:
                    parts = [loc.get('city'), loc.get('region'), loc.get('country')]
                    loc_strings.append(", ".join([p for p in parts if p]))
                
                location_str = "; ".join(loc_strings)
                if not location_str:
                    # Fallback to single location object
                    single_loc = item.get('location', {})
                    parts = [single_loc.get('city'), single_loc.get('region'), single_loc.get('country')]
                    location_str = ", ".join([p for p in parts if p])

                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
            # Check pagination end
            total_items = data.get('data', {}).get('total', 0)
            current_count = len(jobs)
            
            # If the current page returned fewer than limit, we are done
            if len(results) < limit:
                print("[Uber] Reached end of results.")
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[Uber] Request failed: {e}")
            break

    print(f"[Uber] Total jobs found: {len(jobs)}")
    return jobs

