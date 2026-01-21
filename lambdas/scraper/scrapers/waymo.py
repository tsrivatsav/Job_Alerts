from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_waymo(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Waymo Careers.
    Iterates up to 10 pages by modifying the 'page' query parameter.
    Preserves filter arrays (e.g. country_codes[]).
    """
    print(f"[Waymo] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # 1. Parse URL Parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # parse_qs returns lists (e.g. {'country_codes[]': ['US']}). 
    # requests.get handles this format correctly (it sends key=val1&key=val2), 
    # so we copy it directly.
    params = query_params.copy()
    
    # Determine start page (default to 1)
    start_page = int(params.get('page', ['1'])[0])
    
    # Base URL (remove query string)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    PAGES_TO_SCRAPE = 10
    
    # Loop from start_page up to start_page + 10
    for page_num in range(start_page, start_page + PAGES_TO_SCRAPE):
        print(f"[Waymo] Fetching page {page_num}...")
        
        # Update page parameter
        # Note: We overwrite the list with a new single-item list for 'page'
        params['page'] = str(page_num)
        
        try:
            response = session.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Waymo] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards container
            # Based on HTML: <div class="card-body job-search-results-card-body">
            job_cards = soup.find_all('div', class_='job-search-results-card-body')
            
            if not job_cards:
                print(f"[Waymo] No jobs found on page {page_num}. Stopping.")
                break
            
            new_jobs_count = 0
            
            for card in job_cards:
                try:
                    # 1. Extract Title and URL
                    # <h3 class="card-title ..."><a href="...">
                    title_elem = card.find('h3', class_='job-search-results-card-title')
                    if not title_elem:
                        continue
                        
                    link = title_elem.find('a')
                    if not link:
                        continue
                        
                    title = link.get_text(strip=True)
                    full_url = link['href'] # Waymo URLs in href are usually absolute
                    
                    # 2. Extract Location
                    # Look for <li class="job-component-location"> -> <span>
                    location = "Not specified"
                    loc_li = card.find('li', class_='job-component-location')
                    if loc_li:
                        loc_span = loc_li.find('span')
                        if loc_span:
                            location = loc_span.get_text(strip=True)
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"[Waymo] Error parsing card: {e}")
                    continue
            
            print(f"[Waymo] Found {new_jobs_count} jobs on page {page_num}.")
            
            if new_jobs_count == 0:
                break
                
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"[Waymo] Request failed: {e}")
            break

    print(f"[Waymo] Total jobs found: {len(all_jobs)}")
    return all_jobs

