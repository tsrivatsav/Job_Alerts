import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_hrt(url: str = "https://www.hudsonrivertrading.com/careers/") -> List[Dict[str, str]]:
    """
    Scraper for Hudson River Trading (WordPress/HRT Custom).
    Endpoint: /wp-admin/admin-ajax.php
    """
    print(f"[HRT] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'www.hudsonrivertrading.com',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.hudsonrivertrading.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    })

    api_url = "https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php"

    # 2. Construct Payload
    # Replicating the exact filters from your browser inspection.
    # The keys use the "array[]" notation expected by PHP backends.
    
    settings_json = json.dumps({
        "meta_data": [
            {"icon": "", "term": "locations"},
            {"icon": "", "term": "job-category"},
            {"icon": "", "term": "job-type"}
        ],
        "settings": {"hide_job_id": True}
    })

    payload = {
        'action': 'get_hrt_jobs_handler',
        'data[search]': '',
        'setting': settings_json,
        
        # Specific Location Filters
        'data[locations][]': [
            'austin', 
            'bellevue', 
            'boulder', 
            'carteret', 
            'chicago', 
            'new-york', 
            'seattle'
        ],
        
        # Specific Category Filters (C++, Python, Strategy)
        'data[job-category][]': [
            'software-engineeringc', 
            'parent_software-engineeringc', 
            'software-engineeringpython', 
            'strategy-development'
        ],
        
        # Specific Job Type Filters
        'data[job-type][]': [
            'full-time-experienced', 
            'parent_full-time-experienced'
        ]
    }
    
    jobs = []
    print(f"[HRT] Fetching jobs via AJAX...")
        
    try:
        # requests will serialize the lists into: 
        # data[locations][]=austin&data[locations][]=bellevue...
        response = session.post(api_url, data=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[HRT] API Error {response.status_code}")
            return jobs
            
        data = response.json()
            
        if not data:
            print(f"[HRT] No jobs found.")
            return jobs
            
        # 3. Parse Results
        for item in data:
            title = item.get('title')
            html_content = item.get('content', '')
            
            if not html_content:
                continue

            # Parse the inner HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract URL
            link_tag = soup.find('a', class_='hrt-card-title')
            if not link_tag:
                link_tag = soup.find('a', class_='hrt-card-button')
            
            full_url = link_tag['href'] if link_tag else None
            
            # Extract Location (Desktop view only to avoid duplicates)
            location_str = "Unknown"
            meta_div = soup.find('div', class_='hrt-card-meta-desktop')
            
            if meta_div:
                first_ul = meta_div.find('ul', class_='hrt-card-info-list')
                # Ensure we aren't grabbing the category list
                if first_ul and 'second-list' not in first_ul.get('class', []):
                    loc_items = first_ul.find_all('li')
                    locs = [li.get_text(strip=True) for li in loc_items]
                    location_str = ", ".join(locs)

            if full_url:
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
    except Exception as e:
        print(f"[HRT] Request failed: {e}")

    print(f"[HRT] Total jobs found: {len(jobs)}")
    return jobs

