from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote


def scrape_deepmind(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Google DeepMind careers page (Greenhouse).
    Handles pagination automatically.
    URL: https://job-boards.greenhouse.io/deepmind
    """
    
    print(f"[DeepMind] Scraping: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    all_jobs = []
    page = 1
    base_url = url.split('?')[0]  # Remove any existing query params
    
    while True:
        # Build page URL
        page_url = f"{base_url}?page={page}" if page > 1 else base_url
        print(f"[DeepMind] Fetching page {page}: {page_url}")
        
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all job rows
        job_rows = soup.find_all('tr', class_='job-post')
        
        if not job_rows:
            print(f"[DeepMind] No jobs found on page {page}, stopping pagination")
            break
        
        jobs_on_page = 0
        
        for row in job_rows:
            try:
                # Find the link
                link = row.find('a', href=True)
                if not link:
                    continue

                # Extract job URL (already absolute)
                job_url = link['href']

                title_elem = link.find('p', class_='body--medium')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                location_elem = link.find('p', class_='body--metadata')
                location = location_elem.get_text(strip=True) if location_elem else 'Not specified'
                
                all_jobs.append({
                    'title': title,
                    'url': job_url,
                    'location': location
                })
                
                jobs_on_page += 1
                
            except Exception as e:
                print(f"[DeepMind] Error parsing job row: {e}")
                continue
        
        print(f"[DeepMind] Found {jobs_on_page} jobs on page {page}")
        
        # Method 3: Just try next page and see if it has jobs
        # (The while loop will break when no jobs are found)
        if jobs_on_page > 0:
            page += 1
            if page > 50:  # Safety limit
                print("[DeepMind] Reached page limit (50), stopping")
                break
        else:
            break
    
    print(f"[DeepMind] Total jobs found: {len(all_jobs)}")
    return all_jobs

