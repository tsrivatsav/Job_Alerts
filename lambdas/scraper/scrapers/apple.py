from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time

def scrape_apple(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Apple Careers. 
    Iterates through the first 5 pages of results.
    """
    print(f"[Apple] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Parse initial URL to get base path and query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Flatten parameters for the requests library
    # parse_qs returns {'key': ['val']}, we want {'key': 'val'}
    params = {k: v[0] for k, v in query_params.items()}
    
    # Base URL (e.g., https://jobs.apple.com/en-us/search)
    base_search_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    
    # Iterate through the first 5 pages
    for page_num in range(1, 6):
        print(f"[Apple] Fetching page {page_num}...")
        
        # Update the page parameter
        params['page'] = page_num
        
        try:
            response = session.get(base_search_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Apple] Error {response.status_code} on page {page_num}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows based on the class 'job-list-item' provided in HTML
            job_rows = soup.find_all('div', class_=lambda x: x and 'job-list-item' in x)
            
            if not job_rows:
                # If page 1 works but page 5 is empty, we just stop
                print(f"[Apple] No jobs found on page {page_num}. Stopping.")
                break
            
            for row in job_rows:
                try:
                    # 1. Extract Title and URL
                    # Looking for <a class="link-inline ..."> inside <h3>
                    title_link = row.find('a', class_=lambda x: x and 'link-inline' in x)
                    
                    if not title_link:
                        continue
                        
                    title = title_link.get_text(strip=True)
                    
                    relative_url = title_link.get('href')
                    # Build full URL: https://jobs.apple.com + /en-us/details/...
                    full_url = urljoin("https://jobs.apple.com", relative_url)
                    
                    # 2. Extract Location
                    # <div class="... job-title-location"><span id="search-store-name...">Seattle</span></div>
                    location = "Not specified"
                    loc_div = row.find('div', class_=lambda x: x and 'job-title-location' in x)
                    
                    if loc_div:
                        # Sometimes there is a label <span class="a11y">Location</span>, we want the visible text
                        # usually in the span with id starting with 'search-store-name'
                        loc_span = loc_div.find('span', id=lambda x: x and 'search-store-name' in x)
                        if loc_span:
                            location = loc_span.get_text(strip=True)
                        else:
                            # Fallback: get all text and strip "Location" if present
                            location = loc_div.get_text(strip=True).replace("Location", "")
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    
                except Exception as e:
                    print(f"[Apple] Error parsing job row: {e}")
                    continue
            
            # Polite sleep between pages
            time.sleep(1)
            
        except Exception as e:
            print(f"[Apple] Request failed on page {page_num}: {e}")
            break

    print(f"[Apple] Total jobs found: {len(all_jobs)}")
    return all_jobs

