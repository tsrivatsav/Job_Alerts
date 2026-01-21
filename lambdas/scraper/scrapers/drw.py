import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_drw(url: str = "https://drw.com/work-at-drw/listings") -> List[Dict[str, str]]:
    """
    Scraper for DRW.
    Extracts raw job data from the Next.js __NEXT_DATA__ script tag.
    Target URL: https://drw.com/work-at-drw/listings
    """
    print(f"[DRW] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'drw.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[DRW] API Error {response.status_code}")
            return jobs
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find the hidden Next.js JSON blob
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        if not script_tag:
            print("[DRW] Could not find __NEXT_DATA__ script. Site structure might have changed.")
            return jobs
            
        # 2. Parse JSON
        data = json.loads(script_tag.string)
        
        # 3. Navigate the JSON path found in your JS file
        # Path: props -> pageProps -> jobData -> en
        page_props = data.get('props', {}).get('pageProps', {})
        job_data = page_props.get('jobData', {})
        
        # The JS snippet showed: var m = o[x] (where x is 'en')
        english_jobs = job_data.get('en', [])
        
        if not english_jobs:
            print("[DRW] No jobs found in 'jobData.en'.")
            return jobs
            
        # 4. Extract details
        for item in english_jobs:
            # EXTRACT COUNTRIES
            # The JS variable 'career_countries' is an array, e.g., ["United States", "Singapore"]
            countries = item.get('career_countries', [])
            
            # --- FILTER LOGIC ---
            # We check if "United States" is present in the country list.
            if "United States" not in countries:
                continue
            # --------------------
            title = item.get('title')
            slug = item.get('slug')
            
            # Construct URL
            # The JS code uses: "/work-at-drw/listings/" + slug
            full_url = f"https://drw.com/work-at-drw/listings/{slug}"
            
            # Extract Location
            # The JS shows 'locations' is an array of strings
            loc_list = item.get('locations', [])
            location_str = ", ".join(loc_list) if loc_list else "Unknown"
            
            # Optional: Extract Categories or Keywords if needed
            # categories = item.get('career_categories', [])
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[DRW] Extraction failed: {e}")

    print(f"[DRW] Total jobs found: {len(jobs)}")
    return jobs

