import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import re

def scrape_deshaw(url: str = "https://www.deshaw.com/careers") -> List[Dict[str, str]]:
    """
    Scraper for D. E. Shaw.
    Manually constructs URLs from Title + ID to ensure stability.
    """
    print(f"[DE Shaw] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Get Next.js Data
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if not script_tag:
            print("[DE Shaw] Error: __NEXT_DATA__ not found.")
            return jobs
            
        data = json.loads(script_tag.string)
        page_props = data.get('props', {}).get('pageProps', {})
        
        all_raw_jobs = page_props.get('regularJobs', [])
        
        # 2. Extract and Construct
        for item in all_raw_jobs:
            # Use top-level keys which are safer
            title = item.get('displayName')
            job_id = item.get('id')
            
            if not title or not job_id:
                continue

            # --- URL CONSTRUCTION ---
            # Pattern: https://www.deshaw.com/careers/{title-slug}-{id}
            # 1. Lowercase
            slug = title.lower()
            # 2. Remove special characters (keep only alphanumeric and spaces/hyphens)
            slug = re.sub(r'[^a-z0-9\s-]', '', slug)
            # 3. Replace whitespace with single hyphens
            slug = re.sub(r'\s+', '-', slug).strip('-')
            
            full_url = f"https://www.deshaw.com/careers/{slug}-{job_id}"
            # ------------------------
            
            # Extract Location
            # Using top-level 'office' list
            office_list = item.get('office', [])
            locations = [office.get('name') for office in office_list if office.get('name')]
            location_str = ", ".join(locations) if locations else "Unknown"
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[DE Shaw] Extraction failed: {e}")

    print(f"[DE Shaw] Total jobs found: {len(jobs)}")
    return jobs

