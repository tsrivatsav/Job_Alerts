from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote


def scrape_two_sigma(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Two Sigma careers page with pagination.
    URL: https://careers.twosigma.com/careers/OpenRoles/
    """
    
    print(f"[Two Sigma] Scraping: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Parse the base URL to handle existing query params
    parsed_url = urlparse(url)
    base_params = parse_qs(parsed_url.query)
    
    # Flatten params (parse_qs returns lists)
    base_params = {k: v[0] if len(v) == 1 else v for k, v in base_params.items()}
    
    all_jobs = []
    seen_urls = set()
    offset = 0
    
    while True:
        # Update offset
        base_params['jobOffset'] = str(offset)
        
        # Rebuild URL with updated params
        query_string = urlencode(base_params, doseq=True)
        page_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            query_string,
            parsed_url.fragment
        ))
        
        print(f"[Two Sigma] Fetching offset {offset}: {page_url}")
        
        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                print(f"[Two Sigma] Page not found (404), stopping")
                break
            
            if response.status_code >= 400:
                print(f"[Two Sigma] Error {response.status_code}, stopping")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"[Two Sigma] Request failed: {e}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all job articles
        job_articles = soup.select('div.article__header__text')
        
        if not job_articles:
            print(f"[Two Sigma] No jobs found at offset {offset}, stopping")
            break
        
        new_jobs_on_page = 0
        
        for article in job_articles:
            try:
                # Find the title link
                title_link = article.select_one('h3.article__header__text__title a.link')
                
                if not title_link:
                    continue
                
                job_url = title_link.get('href', '')
                
                if not job_url or job_url in seen_urls:
                    continue
                
                seen_urls.add(job_url)
                
                # Get title
                title = title_link.get_text(strip=True)
                
                if not title:
                    continue
                
                # Get location - first span in article__header__content__text
                location = 'Not specified'
                content_text = article.select_one('div.article__header__content__text')
                if content_text:
                    location_span = content_text.find('span', class_='paragraph_inner-span', recursive=False)
                    if not location_span:
                        # Try getting first span
                        spans = content_text.select('span.paragraph_inner-span')
                        if spans:
                            location_span = spans[0]
                    if location_span:
                        location = location_span.get_text(strip=True)
                    if 'United States' not in location:
                        continue  # Skip non-US locations
                
                # Get department and experience from sub-text
                department = None
                experience = None
                sub_text = article.select_one('div.article__header__content__sub-text')
                if sub_text:
                    sub_spans = sub_text.select('span.paragraph_inner-span')
                    if len(sub_spans) >= 1:
                        department = sub_spans[0].get_text(strip=True)
                    if len(sub_spans) >= 2:
                        experience = sub_spans[1].get_text(strip=True)
                    if experience != 'Experienced':
                        continue  # Skip non-experienced roles
                
                all_jobs.append({
                    'title': title,
                    'url': job_url,
                    'location': location
                })
                
                new_jobs_on_page += 1
                
            except Exception as e:
                print(f"[Two Sigma] Error parsing job: {e}")
                continue
        
        print(f"[Two Sigma] Found {new_jobs_on_page} new jobs at offset {offset}")
        
        # No new jobs = end of results
        if new_jobs_on_page == 0:
            print(f"[Two Sigma] No new jobs at offset {offset}, stopping")
            break
        
        # Safety limit
        if offset >= 500:
            print("[Two Sigma] Reached offset limit (500), stopping")
            break
        
        # Increment offset by page size
        offset += int(base_params.get('jobRecordsPerPage', 10))
    
    print(f"[Two Sigma] Total jobs found: {len(all_jobs)}")
    return all_jobs

