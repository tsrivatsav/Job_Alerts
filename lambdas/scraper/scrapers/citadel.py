from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import html
import time

def scrape_citadel(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Citadel careers using WordPress AJAX API.
    """
    print(f"Citadel Scraping: {url}")
    
    # 1. API Endpoint
    api_url = "https://www.citadel.com/wp-admin/admin-ajax.php"
    
    # 2. Parse initial filters from the user's browser URL
    # We strip the '?' params from the input URL to build our POST payload
    parsed_url = urlparse(url)
    url_params = parse_qs(parsed_url.query)
    
    # Flatten parameters (parse_qs returns lists, we want strings)
    # We default 'action' to 'careers_listing_filter' as seen in the payload
    payload_base = {
        'action': 'careers_listing_filter',
        'per_page': '10',
        'sort_order': 'DESC'
    }
    
    # Merge URL params into payload (e.g., experience-filter, location-filter)
    for k, v in url_params.items():
        payload_base[k] = v[0]

    # 3. Headers
    headers = {
        'authority': 'www.citadel.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.citadel.com',
        'referer': url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest', # Critical for WP AJAX
    }
    
    jobs = []
    seen_urls = set()
    current_page = 1
    
    while True:
        print(f"Fetching page {current_page}...")
        
        # Update pagination in payload
        payload = payload_base.copy()
        payload['current_page'] = str(current_page)
        
        try:
            # Use POST with data=payload
            response = requests.post(api_url, headers=headers, data=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"Status Error: {response.status_code}")
                break
                
            data = response.json()
            
            # The API returns HTML inside the 'content' key
            html_content = data.get('content', '')
            total_posts = int(data.get('found_posts', 0))
            
            if not html_content:
                print("No content returned.")
                break
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            job_cards = soup.find_all('a', class_='careers-listing-card')
            
            if not job_cards:
                print(f"No jobs found on page {current_page}.")
                break
                
            new_jobs_count = 0
            
            for card in job_cards:
                try:
                    job_url = card.get('href')
                    if not job_url or job_url in seen_urls:
                        continue
                    
                    seen_urls.add(job_url)
                    
                    # Title is often in 'data-position' attribute or h2
                    # We must unescape HTML entities (e.g., &#038; -> &)
                    title_raw = card.get('data-position')
                    if not title_raw:
                        h2 = card.find('h2')
                        title_raw = h2.get_text(strip=True) if h2 else "Unknown Title"
                        
                    title = html.unescape(title_raw)
                    
                    # Location
                    loc_elem = card.find('span', class_='careers-listing-card__location')
                    location = loc_elem.get_text(strip=True) if loc_elem else None
                    
                    jobs.append({
                        'title': title,
                        'url': job_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            # Check if we should stop
            # If we found no new jobs, or if we have collected all known posts
            if new_jobs_count == 0:
                break
                
            if len(jobs) >= total_posts:
                print(f"Reached total post count ({total_posts}).")
                break
                
            current_page += 1
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            break
            
    print(f"[Citadel] Found {len(jobs)} jobs")
    return jobs

