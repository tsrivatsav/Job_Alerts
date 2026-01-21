from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_rentech(url: str) -> List[Dict[str, str]]:
    """
    Renaissance Technologies scraping logic.
    """
    print(f"RenTech Scraping: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    
    # Find all job listing links
    # They have href containing 'Careers.action' and 'selectedPosition'
    job_links = soup.find_all('a', href=lambda x: x and 'Careers.action' in x and 'selectedPosition' in x)
    
    for job_link in job_links:
        try:
            # Extract job title from the link text
            title = job_link.get_text(strip=True)
            if not title:
                continue
            
            # Build full URL
            relative_url = job_link['href']
            base_url = url.rsplit('/', 1)[0] if '/' in url else url
            full_url = f"https://www.rentec.com{relative_url}"
            
            # Extract location from sibling div
            location = None
            parent_div = job_link.find_parent('div', class_='flex-auto')
            if parent_div:
                location_div = parent_div.find_next_sibling('div')
                if location_div:
                    location = location_div.get_text(strip=True)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location
            })
            
        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue
        
    print(f"[RenTech] Found {len(jobs)} jobs")
    return jobs

