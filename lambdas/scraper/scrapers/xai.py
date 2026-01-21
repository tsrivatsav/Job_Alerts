from typing import List, Dict, Any
from bs4 import BeautifulSoup
import cloudscraper

def scrape_xai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for xAI careers page.
    URL: https://x.ai/careers
    """
    
    print(f"[xAI] Scraping: {url}")
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    response = scraper.get(url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    
    # Find all job links (href contains greenhouse.io/xai/jobs)
    job_links = soup.find_all('a', href=lambda x: x and 'greenhouse.io/xai/jobs' in x)
    
    for link in job_links:
        try:
            job_url = link['href']
            
            # Extract title - span with class 'font-medium' inside the link
            title_elem = link.find('span', class_='font-medium')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Extract location - find the parent container, then look for sibling div with location
            location = 'Not specified'
            parent = link.parent
            
            if parent:
                # Find sibling div containing the location span
                location_div = parent.find('div', class_='flex')
                if location_div and location_div != link.parent:
                    location_span = location_div.find('span', class_='text-secondary')
                    if location_span:
                        location = location_span.get_text(strip=True)
            
            jobs.append({
                'title': title,
                'url': job_url,
                'location': location
            })
            
        except Exception as e:
            print(f"[xAI] Error parsing job: {e}")
            continue
    
    print(f"[xAI] Found {len(jobs)} jobs")
    return jobs

