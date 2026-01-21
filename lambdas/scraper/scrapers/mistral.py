from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup


def scrape_mistral(url: str) -> List[Dict[str, str]]:
    """
    Mistral (Lever) scraping logic.
    """
    print(f"Mistral Scraping: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    
    # Find all job listing links with class 'posting-title'
    job_links = soup.find_all('a', class_='posting-title')
    
    for job_link in job_links:
        try:
            # Extract Title
            # Looking for <h5 data-qa="posting-name">
            title_elem = job_link.find('h5', attrs={'data-qa': 'posting-name'})
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Extract URL
            # The snippet shows an absolute URL: https://jobs.lever.co/mistral/...
            full_url = job_link['href']
            
            # Extract Location
            # Looking for <span class="... location">
            location = None
            location_elem = job_link.find('span', class_=lambda x: x and 'location' in x)
            if location_elem:
                location = location_elem.get_text(strip=True)
            if 'Palo Alto' not in location and 'New York' not in location:
                continue
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location
            })
            
        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue

    print(f"[Mistral] Found {len(jobs)} jobs")
    return jobs

