from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

def scrape_togetherai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Together AI (Greenhouse).
    Single page scraper (no pagination required).
    """
    print(f"[Together AI] Scraping: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        
        # Find all job rows
        # Structure: <tr class="job-post">...</tr>
        job_rows = soup.find_all('tr', class_='job-post')
        
        if not job_rows:
            print("[Together AI] No job rows found.")
            return []
            
        for row in job_rows:
            try:
                link = row.find('a')
                if not link:
                    continue
                
                # Extract URL
                href = link.get('href')
                if not href:
                    continue
                    
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://job-boards.greenhouse.io{href}"
                
                # Extract Title
                # <p class="body body--medium">Title</p>
                title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # Extract Location
                # <p class="body body__secondary body--metadata">Location</p>
                loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
                
            except Exception as e:
                print(f"[Together AI] Error parsing row: {e}")
                continue
        
        print(f"[Together AI] Found {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"[Together AI] Request failed: {e}")
        return []

