from datetime import datetime
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_anthropic(url: str) -> List[Dict[str, str]]:
    """
    Anthropic scraping logic.
    """
    print(f"Anthropic Scraping: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    
    # Find all job listing links
    # They have href starting with /careers/jobs/
    job_links = soup.find_all('a', href=lambda x: x and x.startswith('/careers/jobs/'))
    
    for job_link in job_links:
        try:
            # Extract job title from the jobRole div
            job_role_div = job_link.find('div', class_=lambda x: x and 'jobRole' in x)
            if not job_role_div:
                continue
                
            title_elem = job_role_div.find('p')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Build full URL
            relative_url = job_link['href']
            full_url = f"https://www.anthropic.com{relative_url}"
            
            # Extract location
            location = None
            job_location_div = job_link.find('div', class_=lambda x: x and 'jobLocation' in x)
            if job_location_div:
                location_elem = job_location_div.find('p')
                if location_elem:
                    location = location_elem.get_text(strip=True)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location
            })
            
        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue
    print(f"[Anthropic] Found {len(jobs)} jobs")
    return jobs