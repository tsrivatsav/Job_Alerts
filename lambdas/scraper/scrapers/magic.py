from typing import List, Dict
import requests
from bs4 import BeautifulSoup

def scrape_magic(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Magic.dev careers page.
    """
    print(f"[Magic] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        html_content = response.content.decode('utf-8', errors='replace')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all job listing items
        job_items = soup.find_all('li', class_='border-b')
        
        if not job_items:
            print("[Magic] No job items found.")
            return jobs
        
        for item in job_items:
            try:
                # Find the link
                link = item.find('a', href=True)
                if not link:
                    continue
                
                href = link.get('href')
                if not href or '/careers/' not in href:
                    continue
                
                # Build full URL
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://magic.dev{href}"
                
                # Extract title from h2
                title_elem = link.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                
                # Extract location from the div with location text
                location_elem = link.find('div', class_=lambda x: x and 'text-gray-a11' in x)
                location = location_elem.get_text(strip=True) if location_elem else "Not specified"
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
                
            except Exception as e:
                print(f"[Magic] Error parsing job item: {e}")
                continue
        
    except Exception as e:
        print(f"[Magic] Request failed: {e}")
    
    print(f"[Magic] Total jobs found: {len(jobs)}")
    return jobs
