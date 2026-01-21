from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import time

def scrape_anthropic(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Anthropic (Greenhouse).
    Handles list parameters (departments[], offices[]) correctly.
    """
    print(f"[Anthropic] Scraping: {url}")
    
    session = requests.Session()
    # Headers - REMOVED Accept-Encoding to let requests handle it automatically
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Keep the full list for each key (departments[], offices[], etc.)
    params = query_params.copy()
    
    # Handle pagination
    start_page = int(params.get('page', ['1'])[0])
    if 'page' in params:
        del params['page']
        
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    seen_urls = set()
    current_page = start_page
    
    MAX_PAGES = 10
    
    for _ in range(MAX_PAGES):
        print(f"[Anthropic] Fetching page {current_page}...")
        
        # Add page param
        request_params = params.copy()
        request_params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=request_params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Anthropic] Error {response.status_code}")
                break
            
            # Use response.text (requests automatically decodes)
            # If still having issues, try response.content.decode('utf-8')
            html_content = response.content.decode('utf-8', errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')
            # Find job rows
            job_rows = soup.find_all('tr', class_='job-post')
            
            if not job_rows:
                print(f"[Anthropic] No jobs found on page {current_page}. Stopping.")
                break
            
            new_jobs_count = 0
            
            for row in job_rows:
                try:
                    cell = row.find('td', class_='cell')
                    if not cell:
                        continue
                        
                    link = cell.find('a')
                    if not link:
                        continue
                    
                    href = link.get('href')
                    if not href:
                        continue
                        
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://job-boards.greenhouse.io{href}"
                    
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                    location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                    
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"[Anthropic] Error parsing row: {e}")
                    continue
            
            print(f"[Anthropic] Found {new_jobs_count} new jobs on page {current_page}.")
            
            if new_jobs_count == 0:
                print("[Anthropic] No unique jobs found. Pagination likely finished.")
                break
                
            current_page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[Anthropic] Request failed: {e}")
            break

    print(f"[Anthropic] Total jobs found: {len(all_jobs)}")
    return all_jobs
