from typing import List, Dict, Any
import requests

def scrape_xtx(url: str = "https://api.xtxcareers.com/jobs.json") -> List[Dict[str, str]]:
    """
    Scraper for XTX Markets.
    Fetches JSON data and filters for New York locations.
    """
    print(f"[XTX Markets] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'api.xtxcareers.com',
        'Accept': '*/*',
        'Origin': 'https://www.xtxmarkets.com',
        'Referer': 'https://www.xtxmarkets.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[XTX Markets] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        results = data.get('jobs', [])
        
        print(f"[XTX Markets] Found {len(results)} total global jobs.")
        
        for item in results:
            # 1. Location Filtering
            # The JSON provides a 'location' object and an 'offices' list.
            # We check both to be safe.
            loc_name = item.get('location', {}).get('name', '')
            offices = item.get('offices', [])
            office_names = [o.get('name') for o in offices]
            
            # Combine all location signals
            all_locs = [loc_name] + office_names
            
            # Check if "New York" is in any of the location strings
            is_new_york = any("New York" in loc for loc in all_locs if loc)
            
            if not is_new_york:
                continue
            
            # 2. Extract Details
            title = item.get('title')
            full_url = item.get('absolute_url')
            
            # Construct a clean location string
            location_str = loc_name if loc_name else ", ".join(office_names)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[XTX Markets] Request failed: {e}")

    print(f"[XTX Markets] Total New York jobs found: {len(jobs)}")
    return jobs

