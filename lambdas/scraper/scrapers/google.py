from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time
import re

def scrape_google(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Google Careers.
    Systematic approach using semantic HTML tags and Material Icons.
    Ignores obfuscated CSS classes.
    """
    print(f"[Google] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    })

    # Parse URL to handle pagination loop
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    base_url_parts = list(parsed_url)
    
    all_jobs = []
    page = 1
    
    while True:
        print(f"[Google] Fetching page {page}...")
        
        # Update page parameter
        query_params['page'] = [str(page)]
        new_query_string = urlencode(query_params, doseq=True)
        base_url_parts[4] = new_query_string
        current_page_url = urlunparse(base_url_parts)
        
        try:
            response = session.get(current_page_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # STRATEGY:
            # 1. Find the Job Link first. This is the most unique identifier.
            #    We look for <a> tags with href containing 'jobs/results/'
            job_links = soup.find_all('a', href=lambda h: h and 'jobs/results/' in h)
            
            if not job_links:
                print(f"[Google] No jobs found on page {page}. Stopping.")
                break
                
            jobs_found_on_page = 0
            
            for link in job_links:
                # 2. Identify the Container
                # We walk up to the nearest <li> to get the full context of the card
                card = link.find_parent('li')
                if not card:
                    continue

                # --- URL ---
                relative_url = link['href']
                full_url = f"https://www.google.com/about/careers/applications/{relative_url}"
                
                # Check for duplicates
                if any(j['url'] == full_url for j in all_jobs):
                    continue

                # --- TITLE ---
                # Systematic: The Title is always the H3 heading inside the card.
                title_tag = card.find('h3')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    # Fallback: Extract from aria-label="Learn more about [Title]"
                    aria = link.get('aria-label', '')
                    title = re.sub(r'^(Learn more about|Share)\s+', '', aria)

                # --- LOCATION ---
                # Systematic: Look for the 'place' icon.
                # HTML: <i class="...">place</i> <span class="...">Kirkland, WA</span>
                # We find the <i> tag with text "place", then get its next sibling.
                location_str = "United States" # Default
                
                place_icon = card.find('i', string=re.compile(r'place', re.I))
                if place_icon:
                    # The text is usually in the immediate next sibling span
                    loc_span = place_icon.find_next_sibling('span')
                    if loc_span:
                        location_str = loc_span.get_text(strip=True)
                
                all_jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
                jobs_found_on_page += 1
            
            print(f"[Google] Found {jobs_found_on_page} jobs on page {page}")
            
            if jobs_found_on_page == 0:
                break
            
            # Google often stops pagination around page 5-10 for unauthenticated scraping
            if page >= 10:
                break
                
            page += 1
            time.sleep(2) # Necessary delay to avoid blocks
            
        except Exception as e:
            print(f"[Google] Request failed: {e}")
            break

    print(f"[Google] Total jobs found: {len(all_jobs)}")
    return all_jobs

