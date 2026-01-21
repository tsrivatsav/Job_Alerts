from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_figureai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Figure AI (Greenhouse).
    Iterates up to 10 pages.
    Stops automatically if no new unique jobs are found (duplicate detection).
    """
    print(f"[Figure AI] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Copy existing params (to preserve any filters if they exist)
    params = query_params.copy()
    
    # Determine start page
    start_page = int(params.get('page', ['1'])[0])
    
    # Clean Base URL
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    seen_urls = set()
    PAGES_TO_SCRAPE = 10
    
    for i in range(PAGES_TO_SCRAPE):
        current_page = start_page + i
        print(f"[Figure AI] Fetching page {current_page}...")
        
        # Update page parameter
        params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Figure AI] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows: <tr class="job-post">
            job_rows = soup.find_all('tr', class_='job-post')
            
            if not job_rows:
                print(f"[Figure AI] No job rows found on page {current_page}. Stopping.")
                break
            
            new_jobs_on_page = 0
            
            for row in job_rows:
                try:
                    # Find Main Link
                    link = row.find('a')
                    if not link:
                        continue
                    
                    # Extract URL
                    relative_url = link.get('href')
                    if not relative_url:
                        continue
                        
                    if relative_url.startswith('http'):
                        full_url = relative_url
                    else:
                        full_url = f"https://job-boards.greenhouse.io{relative_url}"
                    
                    # --- DEDUPLICATION CHECK ---
                    # If we have seen this URL before, skip it.
                    # If ALL jobs on this page are skips, we know the server is ignoring pagination.
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # Extract Title: <p class="body body--medium">
                    title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                    
                    # Extract Location: <p class="body body__secondary body--metadata">
                    loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                    location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_on_page += 1
                    
                except Exception as e:
                    print(f"[Figure AI] Error parsing row: {e}")
                    continue
            
            print(f"[Figure AI] Found {new_jobs_on_page} new jobs on page {current_page}.")
            
            # Stop if no new jobs were found (handles the case where page 2 == page 1)
            if new_jobs_on_page == 0:
                print("[Figure AI] No unique jobs found on this page. Pagination likely finished.")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"[Figure AI] Request failed: {e}")
            break

    print(f"[Figure AI] Total jobs found: {len(all_jobs)}")
    return all_jobs

