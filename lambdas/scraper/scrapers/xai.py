from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import time

def scrape_xai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for xAI (Greenhouse).
    Filters by specific departments: Foundation Model, Infrastructure, Product
    """
    print(f"[xAI] Scraping: {url}")
    
    # Define department filter
    ALLOWED_DEPARTMENTS = {
        'Foundation Model',
        'Infrastructure',
        'Product'
    }
    
    session = requests.Session()
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

# Parse URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
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
        print(f"[xAI] Fetching page {current_page}...")
        
        request_params = params.copy()
        request_params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=request_params, timeout=30)
            
            if response.status_code != 200:
                print(f"[xAI] Error {response.status_code}")
                break
            
            html_content = response.content.decode('utf-8', errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find ALL job rows on the page (regardless of department)
            all_job_rows_on_page = soup.find_all('tr', class_='job-post')
            
            # Stop condition: No jobs at all on this page
            if not all_job_rows_on_page:
                print(f"[xAI] No jobs found on page {current_page}. Stopping.")
                break
            
            total_jobs_on_page = len(all_job_rows_on_page)
            new_jobs_on_page = 0
            filtered_jobs_on_page = 0
            
            # Find all department sections
            department_sections = soup.find_all('div', class_='job-posts--table--department')
            
            if not department_sections:
                # Fallback: Try to find job posts directly with section headers
                section_headers = soup.find_all('h3', class_='section-header')
                
                if section_headers:
                    for header in section_headers:
                        department = header.get_text(strip=True)
                        
                        # Find the next sibling that contains job posts
                        next_sibling = header.find_next_sibling()
                        while next_sibling:
                            if next_sibling.name == 'div' and 'job-posts--table' in next_sibling.get('class', []):
                                job_rows = next_sibling.find_all('tr', class_='job-post')
                                
                                for row in job_rows:
                                    # Skip if department not in allowed list
                                    if department not in ALLOWED_DEPARTMENTS:
                                        continue
                                    
                                    filtered_jobs_on_page += 1
                                    job = parse_job_row(row, department, seen_urls)
                                    if job:
                                        all_jobs.append(job)
                                        seen_urls.add(job['url'])
                                        new_jobs_on_page += 1
                                break
                            elif next_sibling.name == 'h3':
                                break
                            next_sibling = next_sibling.find_next_sibling()
            else:
                # Process department sections
                for section in department_sections:
                    dept_header = section.find('h3', class_='section-header')
                    department = dept_header.get_text(strip=True) if dept_header else 'Unknown'
                    
                    job_rows = section.find_all('tr', class_='job-post')
                    
                    for row in job_rows:
                        # Skip if department not in allowed list
                        if department not in ALLOWED_DEPARTMENTS:
                            continue
                        
                        filtered_jobs_on_page += 1
                        job = parse_job_row(row, department, seen_urls)
                        if job:
                            all_jobs.append(job)
                            seen_urls.add(job['url'])
                            new_jobs_on_page += 1
            
            print(f"[xAI] Page {current_page}: {total_jobs_on_page} total jobs, {filtered_jobs_on_page} matching filter, {new_jobs_on_page} new")
            print(f"[xAI] Running total: {len(all_jobs)} jobs")
            
            current_page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[xAI] Request failed: {e}")
            break

    print(f"[xAI] Total jobs found: {len(all_jobs)}")
    return all_jobs


def parse_job_row(row, department: str, seen_urls: set) -> Optional[Dict[str, str]]:
    """Parse a single job row and return job dict or None"""
    try:
        cell = row.find('td', class_='cell')
        if not cell:
            return None
            
        link = cell.find('a')
        if not link:
            return None
        
        href = link.get('href')
        if not href:
            return None
            
        if href.startswith('http'):
            full_url = href
        else:
            full_url = f"https://job-boards.greenhouse.io{href}"
        
        # Skip if already seen
        if full_url in seen_urls:
            return None
        
        # Extract title
        title_elem = link.find('p', class_='body body--medium')
        if not title_elem:
            title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Extract location
        loc_elem = link.find('p', class_='body body__secondary body--metadata')
        if not loc_elem:
            loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
        location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
        
        return {
            'title': title,
            'url': full_url,
            'location': location
        }
        
    except Exception as e:
        print(f"[xAI] Error parsing row: {e}")
        return None
