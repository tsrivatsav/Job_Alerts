from typing import List, Dict, Any
from bs4 import BeautifulSoup
import cloudscraper

def scrape_openai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for OpenAI careers page.
    """
    
    print(f"[OpenAI] Scraping: {url}")
    
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
    
    # Find all job listing links (href starts with /careers/ but not just /careers/search)
    job_links = soup.find_all('a', href=lambda x: x and x.startswith('/careers/') and '/careers/search' not in x)
    
    for job_link in job_links:
        try:
            # Extract job title from h2
            title_elem = job_link.find('h2')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Build full URL
            relative_url = job_link['href']
            full_url = f"https://openai.com{relative_url}"
            
            # Extract location - span that is a DIRECT child of <a>, not inside the div
            location = None
            for child in job_link.children:
                # Check if it's a Tag (not NavigableString) and is a span
                if hasattr(child, 'name') and child.name == 'span':
                    location = child.get_text(strip=True)
                    break
            
            if not location:
                location = 'Not specified'
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location
            })
            
        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue
    
    print(f"[OpenAI] Found {len(jobs)} jobs")
    return jobs

