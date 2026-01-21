from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_reddit(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Reddit (Greenhouse).
    Fix: Correctly handles list parameters (departments[], offices[]) 
    instead of flattening them.
    """
    print(f"[Reddit] Scraping: {url}")
    
    session = requests.Session()
    # Headers exactly as provided
    session.headers.update({
        'Authority': 'job-boards.greenhouse.io',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Referer': url,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # CRITICAL FIX: Do not use [0]. Keep the full list for each key.
    # requests handles {'key[]': ['val1', 'val2']} by sending key[]=val1&key[]=val2
    params = query_params.copy()
    
    # Determine start page from URL or default to 1
    # We remove 'page' from params initially to manage it in the loop
    start_page = int(params.get('page', ['1'])[0])
    if 'page' in params:
        del params['page']
        
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    seen_urls = set()
    current_page = start_page
    
    # Fetch a few pages starting from the user's provided page
    MAX_PAGES = 5 
    
    for _ in range(MAX_PAGES):
        print(f"[Reddit] Fetching page {current_page}...")
        
        # Add page param
        # Note: Greenhouse expects 'page' as a string, not a list
        request_params = params.copy()
        request_params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=request_params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Reddit] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows
            job_rows = soup.find_all('tr', class_='job-post')
            
            if not job_rows:
                print(f"[Reddit] No jobs found on page {current_page}. Stopping.")
                break
            
            new_jobs_count = 0
            
            for row in job_rows:
                try:
                    link = row.find('a')
                    if not link:
                        continue
                    
                    # Extract URL
                    href = link.get('href')
                    if not href:
                        continue
                        
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://job-boards.greenhouse.io{href}"
                    
                    # Deduplication
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # Extract Title
                    title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    # Extract Location
                    loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                    location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"[Reddit] Error parsing row: {e}")
                    continue
            
            print(f"[Reddit] Found {new_jobs_count} new jobs on page {current_page}.")
            
            # If the page returned content but we've seen every single job already,
            # it means the server is ignoring the 'page' parameter (common in Greenhouse).
            if new_jobs_count == 0:
                print("[Reddit] No unique jobs found. Pagination likely finished.")
                break
                
            current_page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[Reddit] Request failed: {e}")
            break

    print(f"[Reddit] Total jobs found: {len(all_jobs)}")
    return all_jobs

