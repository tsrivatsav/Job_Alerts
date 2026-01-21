from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_thinking_machines(url: str) -> List[Dict[str, str]]:
    """
    Thinking Machines scraping logic.
    """
    print(f"Thinking Machines Scraping: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    
    # Find all table rows with class 'job-post'
    job_rows = soup.find_all('tr', class_='job-post')
    
    for row in job_rows:
        try:
            link = row.find('a')
            if not link:
                continue
            
            # Extract Title
            # Looking for <p class="body body--medium">
            title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Extract URL
            # The HTML shows an absolute URL, but we handle potential relative URLs just in case
            href = link['href']
            if href.startswith('http'):
                full_url = href
            else:
                full_url = f"https://thinkingmachines.ai{href}" # Adjust domain if necessary
            
            # Extract Location
            # Looking for <p class="... body--metadata">
            location = None
            location_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
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
            
    print(f"[Thinking Machines] Found {len(jobs)} jobs")
    return jobs

