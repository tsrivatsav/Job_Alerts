import boto3
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import cloudscraper
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import html
import time
import ast
import re
import curl_cffi

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

JOBS_TABLE = os.environ.get('JOBS_TABLE', 'job_scraper_jobs')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

def lambda_handler(event, context):
    """
    Scraper Lambda: Scrapes jobs for a specific company and notifies of new postings.
    """
    company_name = event['company_name']
    url = event['url']
    
    print(f"Scraping jobs for {company_name} at {url}")
    
    try:
        # Scrape jobs using company-specific logic
        jobs = scrape_jobs(company_name, url)
        print(f"Found {len(jobs)} total jobs")
        
        # Check for new jobs
        jobs_table = dynamodb.Table(JOBS_TABLE)
        new_jobs = []
        
        for job in jobs:
            # Check if job URL already exists in database
            response = jobs_table.get_item(Key={'job_url': job['url']})
            
            if 'Item' not in response:
                # New job found!
                new_jobs.append(job)
                
                # Store in DynamoDB
                jobs_table.put_item(Item={
                    'job_url': job['url'],
                    'company_name': company_name,
                    'job_title': job['title'],
                    'location': job.get('location', 'Not specified'),
                    'discovered_at': datetime.utcnow().isoformat(),
                    'notified': True
                })
                
                print(f"New job found: {job['title']}")
        
        # Send notification if new jobs found
        if new_jobs:
            send_notification(company_name, new_jobs)
            print(f"Sent notification for {len(new_jobs)} new jobs")
        else:
            print("No new jobs found")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'company': company_name,
                'total_jobs': len(jobs),
                'new_jobs': len(new_jobs)
            })
        }
        
    except Exception as e:
        print(f"Error scraping {company_name}: {str(e)}")
        raise e


def scrape_jobs(company_name: str, url: str) -> List[Dict[str, str]]:
    """
    Routes to company-specific scraping logic.
    
    Returns:
        List of dicts with 'title' and 'url' keys
        Example: [{'title': 'Software Engineer', 'url': 'https://...'}, ...]
    """
    
    # ============================================
    # COMPANY-SPECIFIC SCRAPER REGISTRY
    # Add your company scrapers here
    # ============================================
    
    scrapers = {
        'Anthropic': scrape_anthropic,
        'OpenAI': scrape_openai,
        'Deepmind': scrape_deepmind,
        'xAI': scrape_xai,
        'Jane Street': scrape_jane_street,
        'Citadel': scrape_citadel,
        'Two Sigma': scrape_two_sigma,
        'Point72': scrape_point72,
        'Renaissance Technologies': scrape_rentech,
        'SSI': scrape_ssi,
        'Thinking Machines': scrape_thinking_machines,
        'Perplexity': scrape_perplexity,
        'Mistral': scrape_mistral,
        'Meta': scrape_meta,
        'Google': scrape_google,
        'Apple': scrape_apple,
        'Microsoft': scrape_microsoft,
        'Amazon': scrape_amazon,
        'Nvidia': scrape_nvidia,
        'Netflix': scrape_netflix,
        'Reddit': scrape_reddit,
        'Spotify': scrape_spotify,
        'Tiktok': scrape_tiktok,
        'Uber': scrape_uber,
        'Waymo': scrape_waymo,
        'FigureAI': scrape_figureai,
        'TogetherAI': scrape_togetherai,
        'HuggingFace': scrape_huggingface,
        'Cohere': scrape_cohere,
        'Reflection AI': scrape_reflectionai,
        'Jump': scrape_jump,
        'HRT': scrape_hrt,
        'IMC': scrape_imc,
        'DRW': scrape_drw,
        'Tower': scrape_tower,
        'Optiver': scrape_optiver,
        'DE Shaw': scrape_deshaw,
        'XTX': scrape_xtx
    }
    
    # Get company-specific scraper or fall back to generic
    scraper = scrapers.get(company_name, scrape_generic)
    return scraper(url)


# ============================================
# PLACEHOLDER SCRAPER IMPLEMENTATIONS
# Replace these with your actual scraping logic
# ============================================

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

def scrape_jane_street(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Jane Street careers page using their JSON API.
    URL: https://www.janestreet.com/jobs/main.json
    """
    
    print(f"[Jane Street] Fetching jobs from API...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Jane Street] Request failed: {e}")
        return []
    
    jobs_data = response.json()
    
    jobs = []
    
    for job in jobs_data:
        try:
            job_id = job.get('id', '')
            title = job.get('position', '')
            location = job.get('city', 'Not specified')
            availability = job.get('availability')
            if location != 'NYC' or availability != 'Full-Time: Experienced':
                continue
            
            # Build job URL
            job_url = f"https://www.janestreet.com/join-jane-street/position/{job_id}/"
            
            jobs.append({
                'title': title,
                'url': job_url,
                'location': location
            })
            
        except Exception as e:
            print(f"[Jane Street] Error parsing job: {e}")
            continue
    
    print(f"[Jane Street] Found {len(jobs)} jobs")
    return jobs

def scrape_citadel(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Citadel careers using WordPress AJAX API.
    """
    print(f"Citadel Scraping: {url}")
    
    # 1. API Endpoint
    api_url = "https://www.citadel.com/wp-admin/admin-ajax.php"
    
    # 2. Parse initial filters from the user's browser URL
    # We strip the '?' params from the input URL to build our POST payload
    parsed_url = urlparse(url)
    url_params = parse_qs(parsed_url.query)
    
    # Flatten parameters (parse_qs returns lists, we want strings)
    # We default 'action' to 'careers_listing_filter' as seen in the payload
    payload_base = {
        'action': 'careers_listing_filter',
        'per_page': '10',
        'sort_order': 'DESC'
    }
    
    # Merge URL params into payload (e.g., experience-filter, location-filter)
    for k, v in url_params.items():
        payload_base[k] = v[0]

    # 3. Headers
    headers = {
        'authority': 'www.citadel.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.citadel.com',
        'referer': url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest', # Critical for WP AJAX
    }
    
    jobs = []
    seen_urls = set()
    current_page = 1
    
    while True:
        print(f"Fetching page {current_page}...")
        
        # Update pagination in payload
        payload = payload_base.copy()
        payload['current_page'] = str(current_page)
        
        try:
            # Use POST with data=payload
            response = requests.post(api_url, headers=headers, data=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"Status Error: {response.status_code}")
                break
                
            data = response.json()
            
            # The API returns HTML inside the 'content' key
            html_content = data.get('content', '')
            total_posts = int(data.get('found_posts', 0))
            
            if not html_content:
                print("No content returned.")
                break
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            job_cards = soup.find_all('a', class_='careers-listing-card')
            
            if not job_cards:
                print(f"No jobs found on page {current_page}.")
                break
                
            new_jobs_count = 0
            
            for card in job_cards:
                try:
                    job_url = card.get('href')
                    if not job_url or job_url in seen_urls:
                        continue
                    
                    seen_urls.add(job_url)
                    
                    # Title is often in 'data-position' attribute or h2
                    # We must unescape HTML entities (e.g., &#038; -> &)
                    title_raw = card.get('data-position')
                    if not title_raw:
                        h2 = card.find('h2')
                        title_raw = h2.get_text(strip=True) if h2 else "Unknown Title"
                        
                    title = html.unescape(title_raw)
                    
                    # Location
                    loc_elem = card.find('span', class_='careers-listing-card__location')
                    location = loc_elem.get_text(strip=True) if loc_elem else None
                    
                    jobs.append({
                        'title': title,
                        'url': job_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"Error parsing card: {e}")
                    continue
            
            # Check if we should stop
            # If we found no new jobs, or if we have collected all known posts
            if new_jobs_count == 0:
                break
                
            if len(jobs) >= total_posts:
                print(f"Reached total post count ({total_posts}).")
                break
                
            current_page += 1
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            break
            
    print(f"[Citadel] Found {len(jobs)} jobs")
    return jobs

def scrape_two_sigma(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Two Sigma careers page with pagination.
    URL: https://careers.twosigma.com/careers/OpenRoles/
    """
    
    print(f"[Two Sigma] Scraping: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Parse the base URL to handle existing query params
    parsed_url = urlparse(url)
    base_params = parse_qs(parsed_url.query)
    
    # Flatten params (parse_qs returns lists)
    base_params = {k: v[0] if len(v) == 1 else v for k, v in base_params.items()}
    
    all_jobs = []
    seen_urls = set()
    offset = 0
    
    while True:
        # Update offset
        base_params['jobOffset'] = str(offset)
        
        # Rebuild URL with updated params
        query_string = urlencode(base_params, doseq=True)
        page_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            query_string,
            parsed_url.fragment
        ))
        
        print(f"[Two Sigma] Fetching offset {offset}: {page_url}")
        
        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                print(f"[Two Sigma] Page not found (404), stopping")
                break
            
            if response.status_code >= 400:
                print(f"[Two Sigma] Error {response.status_code}, stopping")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"[Two Sigma] Request failed: {e}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all job articles
        job_articles = soup.select('div.article__header__text')
        
        if not job_articles:
            print(f"[Two Sigma] No jobs found at offset {offset}, stopping")
            break
        
        new_jobs_on_page = 0
        
        for article in job_articles:
            try:
                # Find the title link
                title_link = article.select_one('h3.article__header__text__title a.link')
                
                if not title_link:
                    continue
                
                job_url = title_link.get('href', '')
                
                if not job_url or job_url in seen_urls:
                    continue
                
                seen_urls.add(job_url)
                
                # Get title
                title = title_link.get_text(strip=True)
                
                if not title:
                    continue
                
                # Get location - first span in article__header__content__text
                location = 'Not specified'
                content_text = article.select_one('div.article__header__content__text')
                if content_text:
                    location_span = content_text.find('span', class_='paragraph_inner-span', recursive=False)
                    if not location_span:
                        # Try getting first span
                        spans = content_text.select('span.paragraph_inner-span')
                        if spans:
                            location_span = spans[0]
                    if location_span:
                        location = location_span.get_text(strip=True)
                    if 'United States' not in location:
                        continue  # Skip non-US locations
                
                # Get department and experience from sub-text
                department = None
                experience = None
                sub_text = article.select_one('div.article__header__content__sub-text')
                if sub_text:
                    sub_spans = sub_text.select('span.paragraph_inner-span')
                    if len(sub_spans) >= 1:
                        department = sub_spans[0].get_text(strip=True)
                    if len(sub_spans) >= 2:
                        experience = sub_spans[1].get_text(strip=True)
                    if experience != 'Experienced':
                        continue  # Skip non-experienced roles
                
                all_jobs.append({
                    'title': title,
                    'url': job_url,
                    'location': location
                })
                
                new_jobs_on_page += 1
                
            except Exception as e:
                print(f"[Two Sigma] Error parsing job: {e}")
                continue
        
        print(f"[Two Sigma] Found {new_jobs_on_page} new jobs at offset {offset}")
        
        # No new jobs = end of results
        if new_jobs_on_page == 0:
            print(f"[Two Sigma] No new jobs at offset {offset}, stopping")
            break
        
        # Safety limit
        if offset >= 500:
            print("[Two Sigma] Reached offset limit (500), stopping")
            break
        
        # Increment offset by page size
        offset += int(base_params.get('jobRecordsPerPage', 10))
    
    print(f"[Two Sigma] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_point72(url: str = "https://careers.point72.com/") -> List[Dict[str, Any]]:
    print(f"[Point72] Scraping URL: {url}")
    
    # --- STEP 1: Parse Filters from the input URL ---
    # The URL parameters (like 'location' or 'area') dictate what we keep.
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    active_filters = {}
    
    # Convert URL params into a clean dictionary of lists
    # Example: location=new york;chicago -> {'location': ['new york', 'chicago']}
    for key, val_list in query_params.items():
        if val_list:
            # Decode (%20 -> space) and split by semicolon
            clean_values = [unquote(x).strip().lower() for x in val_list[0].split(';')]
            active_filters[key] = clean_values

    if active_filters:
        print(f"[Point72] Applying filters: {active_filters}")
    else:
        print("[Point72] No filters detected in URL. Fetching all jobs.")

    # --- STEP 2: Scrape the Raw Data ---
    # We always scrape the base URL because that's where the data lives.
    base_url = "https://careers.point72.com/"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    })
    
    final_jobs = []
    
    try:
        response = session.get(base_url, verify=False, timeout=30)
        html = response.text
        
        # Locate the JavaScript data payload
        search_term = "CSSearchModule.init('"
        start_index = html.find(search_term)
        
        if start_index == -1:
            print("[Point72] Could not find job data in page source.")
            return []
            
        current_idx = start_index + len(search_term)
        extracted_string = ""
        in_escape = False
        
        # Extract the JS string char by char to handle quotes correctly
        while current_idx < len(html):
            char = html[current_idx]
            if in_escape:
                extracted_string += char
                in_escape = False
            else:
                if char == '\\':
                    extracted_string += char
                    in_escape = True
                elif char == "'":
                    break # End of string
                else:
                    extracted_string += char
            current_idx += 1
            
        # --- STEP 3: Sanitize and Parse JSON ---
        # Fix JS-specific escapes (\& and \/) that break Python's parser
        sanitized_str = extracted_string.replace(r'\&', '&').replace(r'\/', '/')
        
        try:
            # Convert JS string literal to Python string
            clean_json_str = ast.literal_eval(f"'{sanitized_str}'")
            data = json.loads(clean_json_str)
            print(f"[Point72] Raw job count: {len(data)}")
            
            # --- STEP 4: Filter and Format Data ---
            for item in data:
                job = item.get('job', {})
                
                # Extract fields based on your JSON snippet
                j_id = job.get('Id')
                j_title = job.get('Name')
                j_url = f"https://careers.point72.com/CSJobDetail?jobId={j_id}"
                
                # Extract filterable fields (normalized to lowercase)
                j_location = str(job.get('Posted_Location__c', '')).lower()
                j_area = str(job.get('Area__c', '')).lower()        # Maps to 'area'
                j_team = str(job.get('Team__c', '')).lower()        # Maps to 'focus'
                j_exp = str(job.get('Experience__c', '')).lower()   # Maps to 'experience'
                
                # Check Filters
                match = True
                
                # 1. Location Filter
                if 'location' in active_filters:
                    # Check if job location contains any of the requested locations
                    if not any(f in j_location for f in active_filters['location']):
                        match = False
                
                # 2. Area Filter (Department)
                if match and 'area' in active_filters:
                    # Strict or partial match for Area
                    if not any(f in j_area for f in active_filters['area']):
                        match = False
                        
                # 3. Focus Filter (Team)
                if match and 'focus' in active_filters:
                    if not any(f in j_team for f in active_filters['focus']):
                        match = False

                # 4. Experience Filter
                if match and 'experience' in active_filters:
                    if not any(f in j_exp for f in active_filters['experience']):
                        match = False
                
                if match and j_id and j_title:
                    final_jobs.append({
                        'title': j_title,
                        'url': j_url,
                        'location': job.get('Posted_Location__c'),
                        'area': job.get('Area__c'),
                        'team': job.get('Team__c'),
                        'experience': job.get('Experience__c')
                    })

        except Exception as e:
            print(f"[Point72] JSON Parsing Error: {e}")
            
    except Exception as e:
        print(f"[Point72] Request Failed: {e}")

    print(f"[Point72] Jobs matching filters: {len(final_jobs)}")
    return final_jobs

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

def scrape_ssi(url: str) -> List[Dict[str, str]]:
    """
    SSI scraping logic.
    """
    return []  # Placeholder for actual implementation

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

def scrape_perplexity(url: str) -> List[Dict[str, str]]:
    """
    Perplexity (Ashby) scraping logic via GraphQL API.
    """
    print(f"Perplexity Scraping: {url}")
    
    # 1. Extract the organization name from the URL
    # Expected format: https://jobs.ashbyhq.com/Perplexity
    org_name = url.rstrip('/').split('/')[-1]
    
    # 2. Setup the GraphQL endpoint and headers
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'Accept': '*/*'
    }
    
    # 3. Define the GraphQL query
    # We reconstruct the query based on the operation name provided
    query = """
    query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
      jobBoard: jobBoardWithTeams(
        organizationHostedJobsPageName: $organizationHostedJobsPageName
      ) {
        jobPostings {
          id
          title
          locationName
          secondaryLocations {
            locationName
          }
          employmentType
        }
      }
    }
    """
    
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {
            "organizationHostedJobsPageName": org_name
        },
        "query": query
    }
    
    jobs = []
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Navigate the JSON response
        # data -> data -> jobBoard -> jobPostings
        job_board = data.get('data', {}).get('jobBoard', {})
        postings = job_board.get('jobPostings', [])
        
        for post in postings:
            title = post.get('title')
            job_id = post.get('id')
            
            # Construct the full URL
            # Ashby URLs usually look like: https://jobs.ashbyhq.com/{org_name}/{job_id}
            full_url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"
            
            # format location (Primary + Secondaries)
            locs = [post.get('locationName')]
            secondaries = post.get('secondaryLocations', [])
            if secondaries:
                for sec in secondaries:
                    if sec.get('locationName'):
                        locs.append(sec.get('locationName'))
            
            # Filter out None and join
            location_str = ", ".join([l for l in locs if l])
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"Error fetching/parsing GraphQL data: {e}")

    print(f"[Perplexity] Found {len(jobs)} jobs")
    return jobs

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

def scrape_meta(url: str) -> List[Dict[str, str]]:
    """
    Meta (Facebook) scraping logic using the Correct 'CareersJobSearchResultsV3DataQuery'.
    """
    print(f"Meta Scraping: {url}")
    
    session = requests.Session()
    
    # 1. Headers: Mimic the exact headers from your network tab
    # Note: We let requests handle 'content-length' automatically
    session.headers.update({
        'authority': 'www.metacareers.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.metacareers.com',
        'referer': url, # Important: Referer must match the search page
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-asbd-id': '359341',
        'x-fb-friendly-name': 'CareersJobSearchResultsV3DataQuery', # Updated friendly name
    })

    # --- Step 1: Fetch LSD Token ---
    print("Fetching tokens...")
    try:
        # We visit the base URL to get the token. 
        # Using the specific search URL as the visit entry point is also safer for referer consistency.
        init_resp = session.get(url)
        init_resp.raise_for_status()
        
        # Regex to find LSD
        # Pattern 1: JSON blob
        match = re.search(r'"LSD".*?"token":"([^"]+)"', init_resp.text)
        lsd_token = match.group(1) if match else None
        
        # Pattern 2: Hidden Input
        if not lsd_token:
            match_input = re.search(r'name="lsd" value="([^"]+)"', init_resp.text)
            lsd_token = match_input.group(1) if match_input else None

        if not lsd_token:
            print("Could not find LSD token.")
            return []
            
        print(f"Got Token: {lsd_token}")
        
        # Update headers with the found token
        session.headers.update({'x-fb-lsd': lsd_token})
        
    except Exception as e:
        print(f"Error extracting token: {e}")
        return []

    # --- Step 2: Parse URL for Search Filters ---
    # We extract the params to rebuild the 'search_input' variable
    parsed = urlparse(url)
    q_params = parse_qs(parsed.query)
    
    q_val = q_params.get('q', [''])[0]
    offices = [v for k, v in q_params.items() if 'offices' in k for v in v]
    roles = [v for k, v in q_params.items() if 'roles' in k for v in v]
    
    # --- Step 3: Iterate (Remote vs Not Remote) ---
    jobs = []
    seen_ids = set()

    # We loop twice to cover both "Remote Only" and standard results if desired.
    # If you only want exactly what's in the URL, remove this loop and check the 'is_remote_only' logic.
    # For now, I will toggle 'is_remote_only' to ensure we get everything.
    for is_remote_only in [False, True]:
        cursor = None
        has_next = True
        page_count = 0
        
        mode_label = "Remote Only" if is_remote_only else "Standard"
        print(f"Scraping mode: {mode_label}")

        while has_next and page_count < 5:
            page_count += 1
            
            # --- Constructing the Variables JSON ---
            # This matches the 'search_input' structure from your payload
            variables_dict = {
                "search_input": {
                    "q": q_val,
                    "divisions": [],
                    "offices": offices,
                    "roles": roles,
                    "leadership_levels": [],
                    "saved_jobs": [],
                    "saved_searches": [],
                    "sub_teams": [],
                    "teams": [],
                    "is_leadership": False,
                    "is_remote_only": is_remote_only,
                    "sort_by_new": False,
                    "results_per_page": None
                }
            }
            
            # Add cursor if we have one (Meta usually accepts 'after' or 'cursor' inside search_input or at top level)
            # For this specific query, the cursor usually goes inside search_input if supported, 
            # or we rely on the fact that we might just get all results if no pagination is strictly enforced by this query type.
            if cursor:
                variables_dict["search_input"]["cursor"] = cursor

            # --- Constructing the Payload ---
            # We include the specific boilerplate fields required by Relay
            payload = {
                'av': '0',
                '__user': '0',
                '__a': '1',
                '__req': '2', # optional, but mimicking the browser
                '__hs': '20465.HYP:comet_plat_default_pkg.2.1...0', # optional
                'dpr': '1',
                '__ccg': 'EXCELLENT',
                '__rev': '1031877983', # This version number changes, if it fails, try removing it
                'lsd': lsd_token,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CareersJobSearchResultsV3DataQuery',
                'variables': json.dumps(variables_dict),
                'server_timestamps': 'true',
                'doc_id': '24330890369943030', # THE KEY ID for this query
            }

            try:
                # POST request with data=payload for application/x-www-form-urlencoded
                resp = session.post("https://www.metacareers.com/graphql", data=payload, timeout=30)
                
                if resp.status_code != 200:
                    print(f"Status Error: {resp.status_code}")
                    # print(resp.text) # Uncomment to debug
                    break
                
                # Clean response (Meta adds "for (;;);" loop protection)
                clean_text = resp.text.replace("for (;;);", "")
                data_json = json.loads(clean_text)
                if 'errors' in data_json:
                    print(f"GraphQL Error: {data_json['errors'][0]['message']}")
                    break

                # Navigate the JSON response
                # Note: The structure changes based on the Friendly Name.
                # For 'CareersJobSearchResultsV3DataQuery', it is usually data -> job_search_results
                data_root = data_json.get('data', {})
                # Try finding the results key (it might be job_search or job_search_results)
                search_results = data_root.get('job_search_with_featured_jobs')
                
                if not search_results:
                    # Sometimes it returns empty if no matches
                    print(f"No results container found for {mode_label}.")
                    break
                
                results_list = search_results.get('all_jobs', [])
                
                if not results_list:
                    print(f"No jobs in list for {mode_label}.")
                    break

                for job in results_list:
                    job_id = job.get('id')
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    
                    title = job.get('title')
                    
                    # Locations parsing
                    loc_objects = job.get('locations', [])
                    loc_str = ", ".join(loc_objects)
                    
                    full_url = f"https://www.metacareers.com/profile/job_details/{job_id}"
                    
                    jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': loc_str
                    })

                # Pagination Logic
                paging = search_results.get('paging', {})
                cursor = paging.get('next_cursor')
                has_next = paging.get('has_next_page', False) and cursor
                
                # Sleep to be polite
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching page: {e}")
                break

    print(f"[Meta] Found {len(jobs)} jobs")
    return jobs

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

def scrape_apple(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Apple Careers. 
    Iterates through the first 5 pages of results.
    """
    print(f"[Apple] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Parse initial URL to get base path and query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Flatten parameters for the requests library
    # parse_qs returns {'key': ['val']}, we want {'key': 'val'}
    params = {k: v[0] for k, v in query_params.items()}
    
    # Base URL (e.g., https://jobs.apple.com/en-us/search)
    base_search_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    
    # Iterate through the first 5 pages
    for page_num in range(1, 6):
        print(f"[Apple] Fetching page {page_num}...")
        
        # Update the page parameter
        params['page'] = page_num
        
        try:
            response = session.get(base_search_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Apple] Error {response.status_code} on page {page_num}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows based on the class 'job-list-item' provided in HTML
            job_rows = soup.find_all('div', class_=lambda x: x and 'job-list-item' in x)
            
            if not job_rows:
                # If page 1 works but page 5 is empty, we just stop
                print(f"[Apple] No jobs found on page {page_num}. Stopping.")
                break
            
            for row in job_rows:
                try:
                    # 1. Extract Title and URL
                    # Looking for <a class="link-inline ..."> inside <h3>
                    title_link = row.find('a', class_=lambda x: x and 'link-inline' in x)
                    
                    if not title_link:
                        continue
                        
                    title = title_link.get_text(strip=True)
                    
                    relative_url = title_link.get('href')
                    # Build full URL: https://jobs.apple.com + /en-us/details/...
                    full_url = urljoin("https://jobs.apple.com", relative_url)
                    
                    # 2. Extract Location
                    # <div class="... job-title-location"><span id="search-store-name...">Seattle</span></div>
                    location = "Not specified"
                    loc_div = row.find('div', class_=lambda x: x and 'job-title-location' in x)
                    
                    if loc_div:
                        # Sometimes there is a label <span class="a11y">Location</span>, we want the visible text
                        # usually in the span with id starting with 'search-store-name'
                        loc_span = loc_div.find('span', id=lambda x: x and 'search-store-name' in x)
                        if loc_span:
                            location = loc_span.get_text(strip=True)
                        else:
                            # Fallback: get all text and strip "Location" if present
                            location = loc_div.get_text(strip=True).replace("Location", "")
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    
                except Exception as e:
                    print(f"[Apple] Error parsing job row: {e}")
                    continue
            
            # Polite sleep between pages
            time.sleep(1)
            
        except Exception as e:
            print(f"[Apple] Request failed on page {page_num}: {e}")
            break

    print(f"[Apple] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_microsoft(url: str) -> List[Dict[str, str]]:
    print(f"[Microsoft] Scraping: {url}")
    
    # --- STEP 1: Parse and Clean Parameters ---
    parsed_url = urlparse(url)
    raw_params = parse_qs(parsed_url.query)
    
    api_params = {}
    
    # Keys that should always be single strings
    single_value_keys = ['location', 'query', 'sort_by', 'domain', 'pid', 'start']
    
    for k, v in raw_params.items():
        raw_val = v[0]
        
        # Handle "filter_" keys (comma-separated lists)
        if k.startswith('filter_') and k not in single_value_keys:
            parts = raw_val.split(',')
            # Double unquote to fix the %252C issue
            clean_parts = [unquote(unquote(p)).strip() for p in parts]
            api_params[k] = clean_parts
        else:
            # Standard single value
            api_params[k] = unquote(raw_val)

    # Defaults
    api_params['domain'] = 'microsoft.com'
    if 'start' not in api_params:
        api_params['start'] = '0'
        
    print(f"[Microsoft] Initial Params: {api_params}")

    # --- STEP 2: Initialize Session ---
    session = curl_cffi.requests.Session(impersonate="chrome120")
    
    # --- STEP 3: Handshake with Retry (Max 3 attempts) ---
    csrf_token = None
    max_retries = 3
    
    print("[Microsoft] Handshake (Getting CSRF)...")
    
    for attempt in range(1, max_retries + 1):
        try:
            init_resp = session.get("https://apply.careers.microsoft.com/careers", timeout=15)
            
            if init_resp.status_code == 200:
                csrf_match = re.search(r'<meta name="_csrf" content="([^"]+)"', init_resp.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"[Microsoft] Token acquired on attempt {attempt}.")
                    break # Success!
                else:
                    print(f"[Microsoft] Attempt {attempt}: No CSRF meta tag found.")
            else:
                print(f"[Microsoft] Attempt {attempt}: HTTP {init_resp.status_code}")
                
        except Exception as e:
            print(f"[Microsoft] Attempt {attempt} failed: {e}")
        
        # Backoff delay (2s, 4s, etc.) if not successful
        if attempt < max_retries:
            delay = 2 * attempt
            print(f"[Microsoft] Retrying in {delay} seconds...")
            time.sleep(delay)

    if not csrf_token:
        print("[Microsoft] Critical: Could not acquire CSRF token after 3 attempts.")
        return []

    # --- STEP 4: Fetch Data with Pagination ---
    api_url = "https://apply.careers.microsoft.com/api/pcsx/search"
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'x-csrf-token': csrf_token,
        'Referer': url,
        'Origin': 'https://apply.careers.microsoft.com'
    }
    
    all_jobs = []
    
    # Ensure current_offset is an integer
    current_offset = int(api_params['start'])
    
    MAX_PAGES = 10
    
    for i in range(MAX_PAGES):
        print(f"[Microsoft] Fetching page {i+1} (Start Index: {current_offset})...")
        
        # Explicitly update the 'start' parameter for this request
        api_params['start'] = str(current_offset)
        
        try:
            resp = session.get(api_url, params=api_params, headers=headers, timeout=30)
            
            if resp.status_code != 200:
                print(f"[Microsoft] API Error: {resp.status_code}")
                break
                
            data = resp.json()
            positions = data.get('data', {}).get('positions', [])
            
            count_found = len(positions)
            
            if count_found == 0:
                print(f"[Microsoft] No more jobs found.")
                break
                
            for pos in positions:
                j_title = pos.get('name')
                j_relative_url = pos.get('positionUrl')
                j_locs = ", ".join(pos.get('locations', []))
                
                all_jobs.append({
                    'title': j_title,
                    'url': f"https://apply.careers.microsoft.com{j_relative_url}",
                    'location': j_locs
                })
            
            print(f"[Microsoft] Page {i+1}: Found {count_found} jobs.")
            
            # --- Pagination Logic ---
            # Increase the offset by the actual number of items found.
            # This ensures we start the next page exactly where the last one ended.
            current_offset += count_found
            
            # Stop if we found fewer than 20 results (standard page size seems to be 20)
            # This saves an unnecessary extra request at the end
            if count_found < 10:
                print("[Microsoft] Reached end of results.")
                break
                
            time.sleep(1.5) # Polite delay
            
        except Exception as e:
            print(f"[Microsoft] Loop Error: {e}")
            break
            
    print(f"[Microsoft] Total jobs collected: {len(all_jobs)}")
    return all_jobs

def scrape_amazon(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Amazon Careers using the JSON API.
    Iterates through 10 pages by modifying the 'offset' parameter.
    """
    print(f"[Amazon] Scraping: {url}")
    
    session = requests.Session()
    
    # Headers based on your network tab
    session.headers.update({
        'Authority': 'amazon.jobs',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://amazon.jobs',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Prepare API Endpoint
    # We switch the path from /en/search to /en/search.json
    parsed_url = urlparse(url)
    api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/en/search.json"
    
    # 2. Parse Query Parameters from input URL
    # parse_qs returns lists like {'offset': ['10']}, we flatten them
    query_params = parse_qs(parsed_url.query)
    params = {k: v[0] for k, v in query_params.items()}
    
    # Ensure result_limit is set (Amazon default is usually 10)
    params['result_limit'] = '10'
    
    # Determine start offset
    start_offset = int(params.get('offset', 0))
    
    all_jobs = []
    PAGES_TO_SCRAPE = 10
    PAGE_SIZE = 10
    
    for i in range(PAGES_TO_SCRAPE):
        current_offset = start_offset + (i * PAGE_SIZE)
        print(f"[Amazon] Fetching page {i+1} (Offset: {current_offset})...")
        
        # Update offset in params
        params['offset'] = str(current_offset)
        
        try:
            response = session.get(api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Amazon] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # Navigate JSON: root -> jobs (list)
            jobs_list = data.get('jobs', [])
            
            if not jobs_list:
                print(f"[Amazon] No jobs found at offset {current_offset}. Stopping.")
                break
            
            for job in jobs_list:
                # Extract fields based on your JSON snippet
                title = job.get('title')
                
                # Path is relative: "/en/jobs/3154759/sr-research-scientist"
                job_path = job.get('job_path')
                full_url = f"https://amazon.jobs{job_path}"
                
                # Location: prefer 'normalized_location', fallback to 'location'
                location = job.get('normalized_location') or job.get('location')
                
                all_jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # Polite sleep to avoid rate limits
            time.sleep(1)
            
        except Exception as e:
            print(f"[Amazon] Request failed: {e}")
            break

    print(f"[Amazon] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_nvidia(url: str) -> List[Dict[str, str]]:
    """
    Scraper for NVIDIA (Workday).
    Pagination: Loops until 'jobPostings' list is empty.
    """
    print(f"[NVIDIA] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://nvidia.wd5.myworkdayjobs.com',
        'Referer': url,
    })

    # 1. Construct API URL
    parsed_url = urlparse(url)
    path_parts = [p for p in parsed_url.path.split('/') if p]
    site_name = path_parts[0] if path_parts else "NVIDIAExternalCareerSite"
    api_url = f"https://{parsed_url.netloc}/wday/cxs/nvidia/{site_name}/jobs"

    # 2. Extract Filters
    query_params = parse_qs(parsed_url.query)
    search_text = query_params.get('q', [''])[0]
    
    # Check if user provided a starting offset in URL, otherwise 0
    current_offset = int(query_params.get('offset', ['0'])[0])
    
    applied_facets = {}
    ignored_params = ['q', 'offset', 'limit']
    for k, v in query_params.items():
        if k not in ignored_params:
            applied_facets[k] = v

    jobs = []
    limit = 20
    
    while True:
        print(f"[NVIDIA] Fetching offset {current_offset}...")
        
        payload = {
            "appliedFacets": applied_facets,
            "limit": limit,
            "offset": current_offset,
            "searchText": search_text
        }
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[NVIDIA] API Error {response.status_code}")
                break
            
            data = response.json()
            job_postings = data.get('jobPostings', [])
            
            # --- PAGINATION LOGIC ---
            # Stop if the list is empty
            if not job_postings:
                print("[NVIDIA] No more jobs returned (empty list). Stopping.")
                break
                
            for post in job_postings:
                title = post.get('title')
                external_path = post.get('externalPath')
                full_url = f"https://{parsed_url.netloc}/{site_name}{external_path}"
                location = post.get('locationsText')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # If we received fewer items than the limit (e.g., asked for 20, got 5),
            # we know this is the last page.
            if len(job_postings) < limit:
                print(f"[NVIDIA] Reached last page (got {len(job_postings)} items).")
                break
                
            # Move to next page
            current_offset += limit
            time.sleep(1)
            
        except Exception as e:
            print(f"[NVIDIA] Request failed: {e}")
            break

    print(f"[NVIDIA] Total jobs scraped: {len(jobs)}")
    return jobs

def scrape_netflix(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Netflix (Explore/Eightfold.ai).
    Uses the API endpoint: /api/apply/v2/jobs
    Iterates by modifying the 'start' parameter.
    """
    print(f"[Netflix] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'explore.jobs.netflix.net',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://explore.jobs.netflix.net',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL for Search Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract query and location from the user provided URL
    search_query = query_params.get('query', [''])[0]
    search_location = query_params.get('location', [''])[0]
    
    # 2. API Configuration
    api_url = "https://explore.jobs.netflix.net/api/apply/v2/jobs"
    
    jobs = []
    start = 0
    num = 10 # Page size
    MAX_PAGES = 10
    page_count = 0
    
    while page_count < MAX_PAGES:
        print(f"[Netflix] Fetching results starting at {start}...")
        
        # 3. Construct Payload Parameters
        # Matches: domain=netflix.com&start=20&num=10&query=...&location=...&sort_by=new
        params = {
            'domain': 'netflix.com',
            'start': start,
            'num': num,
            'query': search_query,
            'location': search_location,
            'sort_by': 'new' 
        }
        
        try:
            response = session.get(api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Netflix] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 4. Extract Jobs
            positions = data.get('positions', [])
            
            if not positions:
                print(f"[Netflix] No jobs found at start {start}. Stopping.")
                break
            
            for pos in positions:
                title = pos.get('name')
                
                # Use canonical URL if available, else build it
                full_url = pos.get('canonicalPositionUrl')
                if not full_url:
                    job_id = pos.get('id')
                    full_url = f"https://explore.jobs.netflix.net/careers/job/{job_id}"
                
                # Locations
                locs = pos.get('locations', [])
                location_str = "; ".join(locs) if locs else pos.get('location')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
            count = len(positions)
            print(f"[Netflix] Found {count} jobs on this page.")
            
            # Pagination Logic
            start += count
            page_count += 1
            
            # If we received fewer items than requested, we are at the end
            if count < num:
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"[Netflix] Request failed: {e}")
            break

    print(f"[Netflix] Total jobs found: {len(jobs)}")
    return jobs

def scrape_reddit(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Reddit (Greenhouse).
    Fix: Correctly handles list parameters (departments[], offices[]) 
    instead of flattening them.
    """
    print(f"[Reddit] Scraping: {url}")
    
    session = requests.Session()
    # Headers exactly as provided
    session.headers.update({
        'Authority': 'job-boards.greenhouse.io',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Referer': url,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # CRITICAL FIX: Do not use [0]. Keep the full list for each key.
    # requests handles {'key[]': ['val1', 'val2']} by sending key[]=val1&key[]=val2
    params = query_params.copy()
    
    # Determine start page from URL or default to 1
    # We remove 'page' from params initially to manage it in the loop
    start_page = int(params.get('page', ['1'])[0])
    if 'page' in params:
        del params['page']
        
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    seen_urls = set()
    current_page = start_page
    
    # Fetch a few pages starting from the user's provided page
    MAX_PAGES = 5 
    
    for _ in range(MAX_PAGES):
        print(f"[Reddit] Fetching page {current_page}...")
        
        # Add page param
        # Note: Greenhouse expects 'page' as a string, not a list
        request_params = params.copy()
        request_params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=request_params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Reddit] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows
            job_rows = soup.find_all('tr', class_='job-post')
            
            if not job_rows:
                print(f"[Reddit] No jobs found on page {current_page}. Stopping.")
                break
            
            new_jobs_count = 0
            
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
                    
                    # Deduplication
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # Extract Title
                    title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    # Extract Location
                    loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                    location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"[Reddit] Error parsing row: {e}")
                    continue
            
            print(f"[Reddit] Found {new_jobs_count} new jobs on page {current_page}.")
            
            # If the page returned content but we've seen every single job already,
            # it means the server is ignoring the 'page' parameter (common in Greenhouse).
            if new_jobs_count == 0:
                print("[Reddit] No unique jobs found. Pagination likely finished.")
                break
                
            current_page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[Reddit] Request failed: {e}")
            break

    print(f"[Reddit] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_spotify(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Spotify using the 'animal/v1/job/search' API.
    Auto-converts URL query params (lists) into the comma-separated format the API expects.
    """
    print(f"[Spotify] Scraping: {url}")
    
    session = requests.Session()
    # Headers exactly as found in your network tab
    session.headers.update({
        'Authority': 'api-dot-new-spotifyjobs-com.nw.r.appspot.com',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.lifeatspotify.com',
        'Referer': 'https://www.lifeatspotify.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL Parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # 2. Format Parameters for API
    # The API expects comma-separated strings for lists.
    # e.g., Input: {'c': ['backend', 'data']} -> API: c="backend,data"
    api_params = {}
    
    for key, values in query_params.items():
        # Join multiple values with commas
        api_params[key] = ",".join(values)

    # 3. API Endpoint
    api_url = "https://api-dot-new-spotifyjobs-com.nw.r.appspot.com/wp-json/animal/v1/job/search"
    
    jobs = []
    
    try:
        print("[Spotify] Fetching jobs from API...")
        response = session.get(api_url, params=api_params, timeout=30)
        
        if response.status_code != 200:
            print(f"[Spotify] API Error {response.status_code}")
            return []
            
        data = response.json()
        
        # 4. Extract Jobs from 'result'
        results = data.get('result', [])
        
        if not results:
            print("[Spotify] No jobs found.")
            return []
            
        for item in results:
            # Title is in 'text'
            title = item.get('text')
            
            # The 'id' in the response corresponds to the URL slug
            # Example ID: "data-scientist-growth-analytics-performance-marketing"
            slug = item.get('id')
            full_url = f"https://www.lifeatspotify.com/jobs/{slug}"
            
            # Locations is a list of objects
            locs = item.get('locations', [])
            loc_names = [l.get('location') for l in locs if l.get('location')]
            location_str = ", ".join(loc_names)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Spotify] Request failed: {e}")

    print(f"[Spotify] Found {len(jobs)} jobs")
    return jobs

def scrape_tiktok(url: str) -> List[Dict[str, str]]:
    """
    Scraper for TikTok Careers (API).
    Parses filters (category, location, recruitment type) from the URL 
    and sends them as JSON lists to the API.
    """
    print(f"[TikTok] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'api.lifeattiktok.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US',
        'Content-Type': 'application/json',
        'Origin': 'https://lifeattiktok.com',
        'Referer': 'https://lifeattiktok.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'website-path': 'tiktok',
    })

    # 1. Parse Filters from Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Helper to parse comma-separated params into lists
    # Example: "CT_1,CT_2" -> ["CT_1", "CT_2"]
    def get_list_param(key):
        val = query_params.get(key, [''])[0]
        if not val:
            return []
        return val.split(',')

    # Extract specific lists expected by the API
    recruitment_ids = get_list_param('recruitment_id_list')
    category_ids = get_list_param('job_category_id_list')
    location_codes = get_list_param('location_code_list')
    subject_ids = get_list_param('subject_id_list')
    
    # Extract Keyword
    # URL uses 'keyword', but sometimes 'q' is used manually
    keyword = query_params.get('keyword', [''])[0] or query_params.get('q', [''])[0]

    # Determine start offset
    start_offset = int(query_params.get('offset', ['0'])[0])

    api_url = "https://api.lifeattiktok.com/api/v1/public/supplier/search/job/posts"
    
    jobs = []
    MAX_PAGES = 50
    PAGE_SIZE = 12
    
    # Loop through pages
    for i in range(MAX_PAGES):
        # Calculate current offset based on start_offset + loop index
        current_offset = start_offset + (i * PAGE_SIZE)
        
        print(f"[TikTok] Fetching page {i+1} (Offset: {current_offset})...")
        
        # 2. Construct Payload
        # We inject the parsed lists directly into the JSON body
        payload = {
            "recruitment_id_list": recruitment_ids if recruitment_ids else ["1"], # Default to "Regular" if missing
            "job_category_id_list": category_ids,
            "subject_id_list": subject_ids,
            "location_code_list": location_codes,
            "keyword": keyword,
            "limit": PAGE_SIZE,
            "offset": current_offset
        }
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[TikTok] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 3. Extract Jobs
            # Structure: data -> data -> job_post_list
            inner_data = data.get('data', {})
            job_list = inner_data.get('job_post_list', [])
            
            if not job_list:
                print(f"[TikTok] No jobs found at offset {current_offset}. Stopping.")
                break
            
            for item in job_list:
                title = item.get('title')
                job_id = item.get('id')
                
                # Construct URL
                full_url = f"https://lifeattiktok.com/search/{job_id}"
                
                # Extract Location
                city_info = item.get('city_info', {})
                location = city_info.get('en_name', 'Not specified')
                
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location
                })
            
            # Check for end of results
            if len(job_list) < PAGE_SIZE:
                print("[TikTok] Reached end of results.")
                break
                
            time.sleep(1) 
            
        except Exception as e:
            print(f"[TikTok] Request failed: {e}")
            break

    print(f"[TikTok] Total jobs found: {len(jobs)}")
    return jobs

def scrape_uber(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Uber Careers.
    Parses URL parameters to construct the complex JSON payload required by the API.
    """
    print(f"[Uber] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'www.uber.com',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://www.uber.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-csrf-token': 'x', # As seen in your headers
    })

    # 1. Parse Input URL Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract Keyword
    search_query = query_params.get('query', [''])[0]
    
    # Extract Simple Lists (Department, Team)
    departments = query_params.get('department', [])
    teams = query_params.get('team', [])
    
    # Extract & Structure Locations
    # URL format: location=USA-California-San Francisco
    # API format: {"country": "USA", "region": "California", "city": "San Francisco"}
    raw_locations = query_params.get('location', [])
    structured_locations = []
    
    for loc in raw_locations:
        parts = loc.split('-')
        # Simple heuristic based on your example: Country-Region-City
        if len(parts) >= 3:
            structured_locations.append({
                "country": parts[0],
                "region": parts[1],
                "city": parts[2]
            })
        elif len(parts) == 1:
            # Fallback for just Country
            structured_locations.append({"country": parts[0]})

    api_url = "https://www.uber.com/api/loadSearchJobsResults?localeCode=en"
    
    jobs = []
    page = 0
    limit = 10
    MAX_PAGES = 10
    
    # Loop through pages (Uber API uses 0-based page index, limit 10)
    while page < MAX_PAGES:
        print(f"[Uber] Fetching page {page}...")
        
        # 2. Construct JSON Payload
        payload = {
            "limit": limit,
            "page": page,
            "params": {
                "query": search_query,
                "department": departments,
                "team": teams,
                "location": structured_locations
            }
        }
        
        # Remove empty keys to keep payload clean
        if not departments: del payload['params']['department']
        if not teams: del payload['params']['team']
        if not structured_locations: del payload['params']['location']
        
        try:
            response = session.post(api_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[Uber] API Error {response.status_code}")
                break
                
            data = response.json()
            
            # 3. Extract Jobs
            # Structure: data -> results (list)
            # Note: The root object has "status": "success", "data": { "results": [...] }
            results = data.get('data', {}).get('results', [])
            
            if not results:
                print(f"[Uber] No jobs found on page {page}. Stopping.")
                break
            
            for item in results:
                title = item.get('title')
                job_id = item.get('id')
                
                # Construct URL
                # Uber URLs are usually /global/en/careers/list/{id}/
                full_url = f"https://www.uber.com/global/en/careers/list/{job_id}/"
                
                # Location Extraction
                # "allLocations": [{"city": "Sunnyvale", "region": "California", "country": "USA"}]
                all_locs = item.get('allLocations', [])
                loc_strings = []
                for loc in all_locs:
                    parts = [loc.get('city'), loc.get('region'), loc.get('country')]
                    loc_strings.append(", ".join([p for p in parts if p]))
                
                location_str = "; ".join(loc_strings)
                if not location_str:
                    # Fallback to single location object
                    single_loc = item.get('location', {})
                    parts = [single_loc.get('city'), single_loc.get('region'), single_loc.get('country')]
                    location_str = ", ".join([p for p in parts if p])

                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
            # Check pagination end
            total_items = data.get('data', {}).get('total', 0)
            current_count = len(jobs)
            
            # If the current page returned fewer than limit, we are done
            if len(results) < limit:
                print("[Uber] Reached end of results.")
                break
                
            page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"[Uber] Request failed: {e}")
            break

    print(f"[Uber] Total jobs found: {len(jobs)}")
    return jobs

def scrape_waymo(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Waymo Careers.
    Iterates up to 10 pages by modifying the 'page' query parameter.
    Preserves filter arrays (e.g. country_codes[]).
    """
    print(f"[Waymo] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # 1. Parse URL Parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # parse_qs returns lists (e.g. {'country_codes[]': ['US']}). 
    # requests.get handles this format correctly (it sends key=val1&key=val2), 
    # so we copy it directly.
    params = query_params.copy()
    
    # Determine start page (default to 1)
    start_page = int(params.get('page', ['1'])[0])
    
    # Base URL (remove query string)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    PAGES_TO_SCRAPE = 10
    
    # Loop from start_page up to start_page + 10
    for page_num in range(start_page, start_page + PAGES_TO_SCRAPE):
        print(f"[Waymo] Fetching page {page_num}...")
        
        # Update page parameter
        # Note: We overwrite the list with a new single-item list for 'page'
        params['page'] = str(page_num)
        
        try:
            response = session.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Waymo] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards container
            # Based on HTML: <div class="card-body job-search-results-card-body">
            job_cards = soup.find_all('div', class_='job-search-results-card-body')
            
            if not job_cards:
                print(f"[Waymo] No jobs found on page {page_num}. Stopping.")
                break
            
            new_jobs_count = 0
            
            for card in job_cards:
                try:
                    # 1. Extract Title and URL
                    # <h3 class="card-title ..."><a href="...">
                    title_elem = card.find('h3', class_='job-search-results-card-title')
                    if not title_elem:
                        continue
                        
                    link = title_elem.find('a')
                    if not link:
                        continue
                        
                    title = link.get_text(strip=True)
                    full_url = link['href'] # Waymo URLs in href are usually absolute
                    
                    # 2. Extract Location
                    # Look for <li class="job-component-location"> -> <span>
                    location = "Not specified"
                    loc_li = card.find('li', class_='job-component-location')
                    if loc_li:
                        loc_span = loc_li.find('span')
                        if loc_span:
                            location = loc_span.get_text(strip=True)
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_count += 1
                    
                except Exception as e:
                    print(f"[Waymo] Error parsing card: {e}")
                    continue
            
            print(f"[Waymo] Found {new_jobs_count} jobs on page {page_num}.")
            
            if new_jobs_count == 0:
                break
                
            time.sleep(1) # Be polite
            
        except Exception as e:
            print(f"[Waymo] Request failed: {e}")
            break

    print(f"[Waymo] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_figureai(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Figure AI (Greenhouse).
    Iterates up to 10 pages.
    Stops automatically if no new unique jobs are found (duplicate detection).
    """
    print(f"[Figure AI] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    })

    # 1. Parse Input URL
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Copy existing params (to preserve any filters if they exist)
    params = query_params.copy()
    
    # Determine start page
    start_page = int(params.get('page', ['1'])[0])
    
    # Clean Base URL
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    all_jobs = []
    seen_urls = set()
    PAGES_TO_SCRAPE = 10
    
    for i in range(PAGES_TO_SCRAPE):
        current_page = start_page + i
        print(f"[Figure AI] Fetching page {current_page}...")
        
        # Update page parameter
        params['page'] = str(current_page)
        
        try:
            response = session.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[Figure AI] Error {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job rows: <tr class="job-post">
            job_rows = soup.find_all('tr', class_='job-post')
            
            if not job_rows:
                print(f"[Figure AI] No job rows found on page {current_page}. Stopping.")
                break
            
            new_jobs_on_page = 0
            
            for row in job_rows:
                try:
                    # Find Main Link
                    link = row.find('a')
                    if not link:
                        continue
                    
                    # Extract URL
                    relative_url = link.get('href')
                    if not relative_url:
                        continue
                        
                    if relative_url.startswith('http'):
                        full_url = relative_url
                    else:
                        full_url = f"https://job-boards.greenhouse.io{relative_url}"
                    
                    # --- DEDUPLICATION CHECK ---
                    # If we have seen this URL before, skip it.
                    # If ALL jobs on this page are skips, we know the server is ignoring pagination.
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    
                    # Extract Title: <p class="body body--medium">
                    title_elem = link.find('p', class_=lambda x: x and 'body--medium' in x)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                    
                    # Extract Location: <p class="body body__secondary body--metadata">
                    loc_elem = link.find('p', class_=lambda x: x and 'body--metadata' in x)
                    location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location
                    })
                    new_jobs_on_page += 1
                    
                except Exception as e:
                    print(f"[Figure AI] Error parsing row: {e}")
                    continue
            
            print(f"[Figure AI] Found {new_jobs_on_page} new jobs on page {current_page}.")
            
            # Stop if no new jobs were found (handles the case where page 2 == page 1)
            if new_jobs_on_page == 0:
                print("[Figure AI] No unique jobs found on this page. Pagination likely finished.")
                break
                
            time.sleep(1)
            
        except Exception as e:
            print(f"[Figure AI] Request failed: {e}")
            break

    print(f"[Figure AI] Total jobs found: {len(all_jobs)}")
    return all_jobs

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

def scrape_huggingface(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Hugging Face (Workable).
    Uses the Workable V3 API: /api/v3/accounts/huggingface/jobs
    """
    print(f"[Hugging Face] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'apply.workable.com',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://apply.workable.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract keyword query
    search_query = query_params.get('query', [''])[0]
    
    # API Endpoint
    api_url = "https://apply.workable.com/api/v3/accounts/huggingface/jobs"
    
    jobs = []
    
    print(f"[Hugging Face] Fetching jobs...")
        
    # 2. Construct Payload
    # We allow broad searching by defaulting lists to empty
    payload = {
        "query": search_query,
        "department": [],
        "location": [{'country': "United States", 'countryCode': "US"}], 
        "workplace": [],
        "worktype": []
    }
        
    try:
        response = session.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[Hugging Face] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # 3. Extract Results
        results = data.get('results', [])
        total_count = data.get('total', 0)
            
        if not results:
            print(f"[Hugging Face] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            shortcode = item.get('shortcode')
            
            # Construct URL
            # Workable job links typically follow this pattern
            full_url = f"https://apply.workable.com/huggingface/j/{shortcode}/"
            
            # Extract Location
            # The API provides both 'location' (object) and 'locations' (list)
            loc_obj = item.get('location', {})
            city = loc_obj.get('city')
            region = loc_obj.get('region') or loc_obj.get('country')
            
            parts = [p for p in [city, region] if p]
            location_str = ", ".join(parts)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Hugging Face] Request failed: {e}")

    print(f"[Hugging Face] Total jobs found: {len(jobs)}")
    return jobs

def scrape_cohere(url: str = "https://jobs.ashbyhq.com/cohere") -> List[Dict[str, str]]:
    """
    Scraper for Cohere (AshbyHQ).
    Uses the Ashby GraphQL API: /api/non-user-graphql?op=ApiJobBoardWithTeams
    """
    print(f"[Cohere] Scraping: {url}")
    
    session = requests.Session()
    
    # Using the specific headers found in your inspection
    session.headers.update({
        'Authority': 'jobs.ashbyhq.com',
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': 'https://jobs.ashbyhq.com',
        'Referer': url,
        # These Apollo headers are often critical for the API to accept the request
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # Extract keyword query to filter results python-side later
    search_query = query_params.get('query', [''])[0].lower()
    
    # API Endpoint
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    # 2. Construct Payload
    # Using the exact query structure provided
    graphql_query = """
    query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
      jobBoard: jobBoardWithTeams(
        organizationHostedJobsPageName: $organizationHostedJobsPageName
      ) {
        teams {
          id
          name
          externalName
          parentTeamId
          __typename
        }
        jobPostings {
          id
          title
          teamId
          locationId
          locationName
          workplaceType
          employmentType
          secondaryLocations {
            ...JobPostingSecondaryLocationParts
            __typename
          }
          compensationTierSummary
          __typename
        }
        __typename
      }
    }

    fragment JobPostingSecondaryLocationParts on JobPostingSecondaryLocation {
      locationId
      locationName
      __typename
    }
    """
    
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {
            "organizationHostedJobsPageName": "cohere"
        },
        "query": graphql_query
    }
    
    jobs = []
    print(f"[Cohere] Fetching jobs...")
        
    try:
        response = session.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[Cohere] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # 3. Extract Results
        # Path based on response: data -> data -> jobBoard -> jobPostings
        job_board = data.get('data', {}).get('jobBoard', {})
        results = job_board.get('jobPostings', [])
            
        if not results:
            print(f"[Cohere] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            
            # Python-side filtering (Ashby API usually returns all jobs for the board)
            if search_query and search_query not in title.lower():
                continue

            job_id = item.get('id')
            emp_type = item.get('employmentType')
            if emp_type != "FullTime":
                continue
            
            # Construct URL
            # Format: https://jobs.ashbyhq.com/cohere/{uuid}?employmentType={type}
            full_url = f"https://jobs.ashbyhq.com/cohere/{job_id}"
            if emp_type:
                full_url += f"?employmentType={emp_type}"
            
            # Extract Location
            primary_loc = item.get('locationName')
            secondary_locs_raw = item.get('secondaryLocations', [])
            
            # Gather all location names
            loc_parts = [primary_loc]
            for sl in secondary_locs_raw:
                if sl.get('locationName'):
                    loc_parts.append(sl.get('locationName'))
            
            # Add workplace type (e.g., Remote) if present
            workplace_type = item.get('workplaceType')
            if workplace_type and workplace_type != "Onsite": 
                 loc_parts.append(workplace_type)

            location_str = ", ".join(filter(None, list(set(loc_parts))))
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Cohere] Request failed: {e}")

    print(f"[Cohere] Total jobs found: {len(jobs)}")
    return jobs

def scrape_reflectionai(url: str = "https://jobs.ashbyhq.com/reflectionai") -> List[Dict[str, str]]:
    print(f"[ReflectionAI] Scraping: {url}")
    
    # 1. Setup Session
    # Ashby uses Cloudflare, so impersonating Chrome is safer.
    session = curl_cffi.requests.Session(impersonate="chrome120")
    
    # 2. Define API Endpoint and Headers
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'content-type': 'application/json',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'accept': '*/*',
        'origin': 'https://jobs.ashbyhq.com',
        'referer': 'https://jobs.ashbyhq.com/reflectionai',
    }
    
    # 3. Define the GraphQL Payload
    # This matches exactly what you saw in the Network tab.
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {
            "organizationHostedJobsPageName": "reflectionai"
        },
        "query": """query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
          jobBoard: jobBoardWithTeams(
            organizationHostedJobsPageName: $organizationHostedJobsPageName
          ) {
            teams {
              id
              name
              externalName
              parentTeamId
              __typename
            }
            jobPostings {
              id
              title
              teamId
              locationId
              locationName
              workplaceType
              employmentType
              secondaryLocations {
                ...JobPostingSecondaryLocationParts
                __typename
              }
              compensationTierSummary
              __typename
            }
            __typename
          }
        }

        fragment JobPostingSecondaryLocationParts on JobPostingSecondaryLocation {
          locationId
          locationName
          __typename
        }"""
    }

    all_jobs = []

    try:
        # 4. Make the POST Request
        response = session.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[ReflectionAI] API Error: {response.status_code}")
            print(response.text)
            return []
            
        data = response.json()
        
        # 5. Extract Data
        # Structure: data -> data -> jobBoard -> jobPostings
        job_list = data.get('data', {}).get('jobBoard', {}).get('jobPostings', [])
        
        print(f"[ReflectionAI] Found {len(job_list)} jobs.")
        
        for job in job_list:
            j_id = job.get('id')
            title = job.get('title')
            
            # Construct URL
            # Ashby URLs are standard: base_url + /job_id
            full_url = f"https://jobs.ashbyhq.com/reflectionai/{j_id}"
            
            # Handle Locations (Primary + Secondary)
            locations = []
            if job.get('locationName'):
                locations.append(job.get('locationName'))
                
            for sec in job.get('secondaryLocations', []):
                sec_name = sec.get('locationName')
                if sec_name and sec_name not in locations:
                    locations.append(sec_name)
            
            location_str = ", ".join(locations)
            
            all_jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[ReflectionAI] Request failed: {e}")

    print(f"[ReflectionAI] Total jobs collected: {len(all_jobs)}")
    return all_jobs

def scrape_jump(url: str = "https://www.jumptrading.com/careers") -> List[Dict[str, str]]:
    """
    Scraper for Jump Trading (Greenhouse).
    Uses the Greenhouse Board API: https://boards-api.greenhouse.io/v1/boards/jumptrading/jobs
    """
    print(f"[Jump Trading] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'boards-api.greenhouse.io',
        'Accept': '*/*',
        'Content-Type': 'application/json',
        'Origin': 'https://www-webflow.jumptrading.com',
        'Referer': 'https://www-webflow.jumptrading.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # 1. Parse Input Filters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    search_query = query_params.get('query', [''])[0].lower()
    
    # 2. API Endpoint
    # Greenhouse allows fetching all jobs for a board in one GET request.
    # We add ?content=true if we wanted descriptions, but for listing we don't need it.
    api_url = "https://boards-api.greenhouse.io/v1/boards/jumptrading/jobs"
    
    jobs = []
    print(f"[Jump Trading] Fetching jobs via API...")
        
    try:
        # Note: Greenhouse uses GET, not POST
        response = session.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"[Jump Trading] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # 3. Extract Results
        # Greenhouse returns a dictionary with a "jobs" list
        results = data.get('jobs', [])
            
        if not results:
            print(f"[Jump Trading] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            
            # Python-side filtering
            if search_query and search_query not in title.lower():
                continue
            
            # Extract URL
            # The API returns 'absolute_url' which directs to the public job page
            full_url = item.get('absolute_url')
            
            # Fallback if absolute_url is missing, construct using ID
            if not full_url:
                job_id = item.get('id')
                # Based on the user provided sample: 
                full_url = f"https://www.jumptrading.com/hr/job?gh_jid={job_id}"
            
            # Extract Location
            # Location is an object: "location": { "name": "Chicago" }
            loc_obj = item.get('location', {})
            location_str = loc_obj.get('name', 'Unknown')
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Jump Trading] Request failed: {e}")

    print(f"[Jump Trading] Total jobs found: {len(jobs)}")
    return jobs

def scrape_hrt(url: str = "https://www.hudsonrivertrading.com/careers/") -> List[Dict[str, str]]:
    """
    Scraper for Hudson River Trading (WordPress/HRT Custom).
    Endpoint: /wp-admin/admin-ajax.php
    """
    print(f"[HRT] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'www.hudsonrivertrading.com',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.hudsonrivertrading.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    })

    api_url = "https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php"

    # 2. Construct Payload
    # Replicating the exact filters from your browser inspection.
    # The keys use the "array[]" notation expected by PHP backends.
    
    settings_json = json.dumps({
        "meta_data": [
            {"icon": "", "term": "locations"},
            {"icon": "", "term": "job-category"},
            {"icon": "", "term": "job-type"}
        ],
        "settings": {"hide_job_id": True}
    })

    payload = {
        'action': 'get_hrt_jobs_handler',
        'data[search]': '',
        'setting': settings_json,
        
        # Specific Location Filters
        'data[locations][]': [
            'austin', 
            'bellevue', 
            'boulder', 
            'carteret', 
            'chicago', 
            'new-york', 
            'seattle'
        ],
        
        # Specific Category Filters (C++, Python, Strategy)
        'data[job-category][]': [
            'software-engineeringc', 
            'parent_software-engineeringc', 
            'software-engineeringpython', 
            'strategy-development'
        ],
        
        # Specific Job Type Filters
        'data[job-type][]': [
            'full-time-experienced', 
            'parent_full-time-experienced'
        ]
    }
    
    jobs = []
    print(f"[HRT] Fetching jobs via AJAX...")
        
    try:
        # requests will serialize the lists into: 
        # data[locations][]=austin&data[locations][]=bellevue...
        response = session.post(api_url, data=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[HRT] API Error {response.status_code}")
            return jobs
            
        data = response.json()
            
        if not data:
            print(f"[HRT] No jobs found.")
            return jobs
            
        # 3. Parse Results
        for item in data:
            title = item.get('title')
            html_content = item.get('content', '')
            
            if not html_content:
                continue

            # Parse the inner HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract URL
            link_tag = soup.find('a', class_='hrt-card-title')
            if not link_tag:
                link_tag = soup.find('a', class_='hrt-card-button')
            
            full_url = link_tag['href'] if link_tag else None
            
            # Extract Location (Desktop view only to avoid duplicates)
            location_str = "Unknown"
            meta_div = soup.find('div', class_='hrt-card-meta-desktop')
            
            if meta_div:
                first_ul = meta_div.find('ul', class_='hrt-card-info-list')
                # Ensure we aren't grabbing the category list
                if first_ul and 'second-list' not in first_ul.get('class', []):
                    loc_items = first_ul.find_all('li')
                    locs = [li.get_text(strip=True) for li in loc_items]
                    location_str = ", ".join(locs)

            if full_url:
                jobs.append({
                    'title': title,
                    'url': full_url,
                    'location': location_str
                })
            
    except Exception as e:
        print(f"[HRT] Request failed: {e}")

    print(f"[HRT] Total jobs found: {len(jobs)}")
    return jobs

def scrape_imc(url: str) -> List[Dict[str, str]]:
    print(f"[IMC] Scraping: {url}")
    
    # --- STEP 1: Parse Filters ---
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    
    # Extract filters (clean & lowercase)
    filter_depts = [x.strip().lower() for x in params.get('jobDepartments', [''])[0].split(',') if x]
    filter_offices = [x.strip().lower() for x in params.get('jobOffices', [''])[0].split(',') if x]
    filter_types = [x.strip().lower() for x in params.get('jobTypes', [''])[0].split(',') if x]

    print(f"[IMC] Active Filters: Depts={filter_depts}, Offices={filter_offices}")

    # --- STEP 2: Setup Session ---
    session = curl_cffi.requests.Session(impersonate="chrome120")
    base_url = "https://www.imc.com/us/search-careers"
    
    all_jobs = []
    seen_ids = set()
    
    req_params = {'page': '1'}
    MAX_PAGES = 10
    
    for page in range(1, MAX_PAGES + 1):
        print(f"[IMC] Fetching Page {page}...")
        req_params['page'] = str(page)
        
        try:
            response = session.get(base_url, params=req_params, timeout=30)
            html = response.text
            
            # --- STEP 3: Robust JSON Extraction ---
            
            # Marker: \"jobs\":[  (This is how it appears in the Next.js JS stream)
            # Indices: \ (0), " (1), j (2), o (3), b (4), s (5), \ (6), " (7), : (8), [ (9)
            marker = r'\"jobs\":['
            start_idx = html.find(marker)
            
            jobs_data = []
            
            if start_idx != -1:
                # We start extracting exactly at the '[' character
                # The marker length is 10 characters. Index 9 is the '['.
                # So start_idx + 9 is the index of '['.
                array_start_idx = start_idx + 9
                
                # Check to be safe
                if html[array_start_idx] != '[':
                    # In case of slight variations, look for the first [ after marker
                    array_start_idx = html.find('[', start_idx)
                
                if array_start_idx != -1:
                    bracket_count = 0
                    extracted_str = ""
                    found_end = False
                    
                    # Loop starting from the first '['
                    for i in range(array_start_idx, len(html)):
                        char = html[i]
                        extracted_str += char
                        
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                        
                        # Break only if we have closed the main array
                        if bracket_count == 0:
                            found_end = True
                            break
                    
                    if found_end:
                        try:
                            # Sanitize the extracted string
                            # It is a JS string literal content, so quotes are escaped (\")
                            # We need to turn \" into " and \\ into \
                            clean_json_str = extracted_str.replace('\\"', '"').replace('\\\\', '\\')
                            
                            jobs_data = json.loads(clean_json_str)
                            print(f"[IMC] Successfully parsed {len(jobs_data)} jobs.")
                        except json.JSONDecodeError:
                            # Fallback: Try raw load (sometimes Next.js doesn't double escape simple structures)
                            try:
                                jobs_data = json.loads(extracted_str)
                                print("[IMC] Parsed raw JSON (no unescape needed).")
                            except:
                                print("[IMC] Failed to parse JSON blob.")
            else:
                print(f"[IMC] Marker not found on page {page}. (Page might be empty or layout changed)")

            # If we still have no data, check for bot block
            if not jobs_data and "Just a moment" in html:
                print("[IMC] Blocked by Cloudflare.")
                break
                
            if not jobs_data:
                break

            # --- STEP 4: Filter & Add ---
            added_count = 0
            
            for item in jobs_data:
                j_id = str(item.get('id'))
                if j_id in seen_ids: continue
                
                j_title = item.get('title', 'Unknown')
                
                # Extract locations (list of objects)
                j_offices_list = item.get('offices', [])
                j_offices_str = [o.get('name', '').lower() for o in j_offices_list]
                
                # Extract Departments & Types
                j_tags = []
                for d in item.get('departments', []):
                    j_tags.append(d.get('name', '').lower())
                for m in item.get('metadata', []):
                    val = m.get('value')
                    if val: j_tags.append(str(val).lower())
                
                # --- FILTERS ---
                
                # 1. Office
                if filter_offices:
                    if not any(o in filter_offices for o in j_offices_str):
                        continue
                        
                # 2. Dept
                if filter_depts:
                    match = False
                    for tag in j_tags:
                        if any(d in tag for d in filter_depts):
                            match = True; break
                    if not match: continue

                # 3. Type
                if filter_types:
                    match = False
                    for tag in j_tags:
                        if any(t in tag for t in filter_types):
                            match = True; break
                    if not match: continue

                # Valid Job
                seen_ids.add(j_id)
                
                # URL Construction
                # Remove special chars for slug
                slug = re.sub(r'[^a-z0-9-]', '', j_title.lower().replace(' ', '-'))
                full_url = f"https://www.imc.com/us/careers/{slug}/{j_id}"
                
                all_jobs.append({
                    'title': j_title,
                    'url': full_url,
                    'location': "; ".join([o.get('name') for o in j_offices_list])
                })
                added_count += 1
            
            print(f"[IMC] Page {page}: Added {added_count} jobs.")
            
            if len(jobs_data) < 10:
                print("[IMC] Reached end of data.")
                break
                
            time.sleep(1)

        except Exception as e:
            print(f"[IMC] Error on page {page}: {e}")
            break
            
    print(f"[IMC] Total jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_drw(url: str = "https://drw.com/work-at-drw/listings") -> List[Dict[str, str]]:
    """
    Scraper for DRW.
    Extracts raw job data from the Next.js __NEXT_DATA__ script tag.
    Target URL: https://drw.com/work-at-drw/listings
    """
    print(f"[DRW] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'drw.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[DRW] API Error {response.status_code}")
            return jobs
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find the hidden Next.js JSON blob
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        if not script_tag:
            print("[DRW] Could not find __NEXT_DATA__ script. Site structure might have changed.")
            return jobs
            
        # 2. Parse JSON
        data = json.loads(script_tag.string)
        
        # 3. Navigate the JSON path found in your JS file
        # Path: props -> pageProps -> jobData -> en
        page_props = data.get('props', {}).get('pageProps', {})
        job_data = page_props.get('jobData', {})
        
        # The JS snippet showed: var m = o[x] (where x is 'en')
        english_jobs = job_data.get('en', [])
        
        if not english_jobs:
            print("[DRW] No jobs found in 'jobData.en'.")
            return jobs
            
        # 4. Extract details
        for item in english_jobs:
            # EXTRACT COUNTRIES
            # The JS variable 'career_countries' is an array, e.g., ["United States", "Singapore"]
            countries = item.get('career_countries', [])
            
            # --- FILTER LOGIC ---
            # We check if "United States" is present in the country list.
            if "United States" not in countries:
                continue
            # --------------------
            title = item.get('title')
            slug = item.get('slug')
            
            # Construct URL
            # The JS code uses: "/work-at-drw/listings/" + slug
            full_url = f"https://drw.com/work-at-drw/listings/{slug}"
            
            # Extract Location
            # The JS shows 'locations' is an array of strings
            loc_list = item.get('locations', [])
            location_str = ", ".join(loc_list) if loc_list else "Unknown"
            
            # Optional: Extract Categories or Keywords if needed
            # categories = item.get('career_categories', [])
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[DRW] Extraction failed: {e}")

    print(f"[DRW] Total jobs found: {len(jobs)}")
    return jobs

def scrape_tower(base_url: str = "https://job-boards.greenhouse.io/embed/job_board") -> List[Dict[str, str]]:
    """
    Scraper for Tower Research Capital (Greenhouse Embed).
    Uses the internal API endpoint with specific validity tokens and filters.
    """
    print(f"[Tower Research] Scraping via API...")
    
    session = requests.Session()
    
    # EXACT Headers from your inspection
    session.headers.update({
        'Authority': 'job-boards.greenhouse.io',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Origin': 'https://job-boards.greenhouse.io', # Often required for these embeds
        'Referer': 'https://job-boards.greenhouse.io/embed/job_board?for=towerresearchcapital',
    })

    # The Endpoint
    api_url = "https://job-boards.greenhouse.io/embed/job_board"
    
    # EXACT Parameters from your payload
    # Note: For 'offices[]' to appear as 'offices[]=' in the URL, we use the key 'offices[]'
    # requests handles lists by repeating the key.
    params = {
        'for': 'towerresearchcapital',
        'validityToken': 'SbNJ9SquY5jgTg62zTKX5-8wNm_t4iGIkm8YhnVBEohc8F0xgrH7ifNu2RStOmpWbe5xFG8ecT_d3dR4xmZ4JLM3XiO-NlOdrC_2LTefIIImeAtwQKOnuCPWXzMsa0gNNR_SN4gJDUDxx4oM9zKJk3WnlYdaBrGzJ_kr6oIw8jiX07lnZkVBleVakUGLib7pgvYuHWCfWQ47dBueKDscjiyLWs0ldVVnm8jI_FEIBjUqHL7yMz0LObzk7c76tuW_1w3tj8xIu3FdU5JK8hmPfB31b9VbVjCwYPcFUJP-vktbHwZ2YqlbYBB5eHYXUeco-fWUFZekIJF2XOi3YbrR3g==',
        
        # Office Filters (IDs)
        'offices[]': [
            '1251', '1250', '1249', '229704', '211963'
        ],
        
        # Department Filters (IDs)
        'departments[]': [
            '2129', '151551', '2124', '31301'
        ],
        
        # Critical parameter to force JSON response instead of HTML
        '_data': 'routes/embed.job_board'
    }
    
    jobs = []
        
    try:
        response = session.get(api_url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"[Tower Research] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        
        # Extract Results
        # Path: root -> jobPosts -> data
        job_posts = data.get('jobPosts', {})
        results = job_posts.get('data', [])
        total_count = job_posts.get('total', 0)
            
        if not results:
            print(f"[Tower Research] No jobs found.")
            return jobs
            
        for item in results:
            title = item.get('title')
            
            # The API returns 'absolute_url' which points to the company's career page wrapper
            full_url = item.get('absolute_url')
            
            # Extract Location
            # In this response, location is a simple string: "New York"
            location_str = item.get('location', "Unknown")
            
            # Optional: Department extraction if needed
            # dept_name = item.get('department', {}).get('name')
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[Tower Research] Request failed: {e}")

    print(f"[Tower Research] Total jobs found: {len(jobs)}")
    return jobs

def scrape_optiver(base_url: str = "https://optiver.com/working-at-optiver/career-opportunities/") -> List[Dict[str, str]]:
    print(f"[Optiver] Starting scraper...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })

    # --- STEP 1: Extract Nonce from 'jobArchiveData' ---
    print(f"[Optiver] Fetching main page to extract dynamic nonce...")
    nonce = None
    
    try:
        response = session.get(base_url, timeout=30)
        
        # Regex explanation:
        # 1. Find 'var jobArchiveData'
        # 2. Match the opening bracket '{' and any characters/newlines [\s\S]*? until...
        # 3. We find "nonce": "CAPTURE_THIS"
        pattern = r'var\s+jobArchiveData\s*=\s*\{[\s\S]*?"nonce"\s*:\s*"([^"]+)"'
        
        match = re.search(pattern, response.text)
        
        if match:
            nonce = match.group(1)
            print(f"[Optiver] Success! Found Nonce: {nonce}")
        else:
            print("[Optiver] WARNING: Could not find 'jobArchiveData' nonce.")
            return []

    except Exception as e:
        print(f"[Optiver] Failed to fetch career page: {e}")
        return []

    # --- STEP 2: Scrape API ---
    api_url = "https://optiver.com/wp-admin/admin-ajax.php"
    
    session.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://optiver.com',
        'Referer': base_url
    })

    target_locations = [
        "New York", "Chicago", "Austin", "Durham", 
        "Jersey City", "Secaucus", "United States"
    ]

    all_jobs = []
    current_page = 1
    max_pages = 1
    
    while current_page <= max_pages:
        print(f"[Optiver] Fetching API page {current_page}...")

        payload = {
            "numberposts": "10",
            "paged": str(current_page),
            "viewmode": "list",
            "search_target": "title,excerpt",
            "taxonomy_relation": "AND",
            "search_relation": "AND",
            "show_load_more": "1",
            "show_pagination": "1",
            "show_sort": "0",
            "orderby": "date",
            "order": "DESC",
            "layout_style": "default",
            "posts_per_page": "10",
            
            # Map the extracted 'nonce' to the parameter 'job_archive_nonce'
            "job_archive_nonce": nonce, 
            
            "show_levels": "1",
            "show_departments": "1",
            "show_offices": "1",
            "show_search": "1",
            "action": "job_archive_get_posts",
            "level": "experienced",
            "department": "", 
            "office": "",
            "search": ""
        }

        try:
            response = session.post(api_url, data=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"[Optiver] API Error {response.status_code}")
                break
                
            data = response.json()
            
            if not data.get('success'):
                print(f"[Optiver] API rejected request. Nonce '{nonce}' might be invalid.")
                break

            max_pages = data.get('max_num_pages', 1)
            results = data.get('result', [])
            
            if not results:
                break
                
            for item in results:
                # Extract Office Terms
                office_terms = item.get('taxonomies', {}).get('office', {}).get('terms', [])
                job_cities = [t.get('name') for t in office_terms]
                
                # Filter for US locations
                if any(city in target_locations for city in job_cities):
                    
                    title = item.get('title')
                    full_url = item.get('permalink')
                    location_str = ", ".join(job_cities)
                    
                    all_jobs.append({
                        'title': title,
                        'url': full_url,
                        'location': location_str
                    })

            current_page += 1
            
        except Exception as e:
            print(f"[Optiver] Error processing page: {e}")
            break

    print(f"[Optiver] Total US jobs found: {len(all_jobs)}")
    return all_jobs

def scrape_deshaw(url: str = "https://www.deshaw.com/careers") -> List[Dict[str, str]]:
    """
    Scraper for D. E. Shaw.
    Manually constructs URLs from Title + ID to ensure stability.
    """
    print(f"[DE Shaw] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Get Next.js Data
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if not script_tag:
            print("[DE Shaw] Error: __NEXT_DATA__ not found.")
            return jobs
            
        data = json.loads(script_tag.string)
        page_props = data.get('props', {}).get('pageProps', {})
        
        all_raw_jobs = page_props.get('regularJobs', [])
        
        # 2. Extract and Construct
        for item in all_raw_jobs:
            # Use top-level keys which are safer
            title = item.get('displayName')
            job_id = item.get('id')
            
            if not title or not job_id:
                continue

            # --- URL CONSTRUCTION ---
            # Pattern: https://www.deshaw.com/careers/{title-slug}-{id}
            # 1. Lowercase
            slug = title.lower()
            # 2. Remove special characters (keep only alphanumeric and spaces/hyphens)
            slug = re.sub(r'[^a-z0-9\s-]', '', slug)
            # 3. Replace whitespace with single hyphens
            slug = re.sub(r'\s+', '-', slug).strip('-')
            
            full_url = f"https://www.deshaw.com/careers/{slug}-{job_id}"
            # ------------------------
            
            # Extract Location
            # Using top-level 'office' list
            office_list = item.get('office', [])
            locations = [office.get('name') for office in office_list if office.get('name')]
            location_str = ", ".join(locations) if locations else "Unknown"
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[DE Shaw] Extraction failed: {e}")

    print(f"[DE Shaw] Total jobs found: {len(jobs)}")
    return jobs

def scrape_xtx(url: str = "https://api.xtxcareers.com/jobs.json") -> List[Dict[str, str]]:
    """
    Scraper for XTX Markets.
    Fetches JSON data and filters for New York locations.
    """
    print(f"[XTX Markets] Scraping: {url}")
    
    session = requests.Session()
    session.headers.update({
        'Authority': 'api.xtxcareers.com',
        'Accept': '*/*',
        'Origin': 'https://www.xtxmarkets.com',
        'Referer': 'https://www.xtxmarkets.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    })
    
    jobs = []
    
    try:
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[XTX Markets] API Error {response.status_code}")
            return jobs
            
        data = response.json()
        results = data.get('jobs', [])
        
        print(f"[XTX Markets] Found {len(results)} total global jobs.")
        
        for item in results:
            # 1. Location Filtering
            # The JSON provides a 'location' object and an 'offices' list.
            # We check both to be safe.
            loc_name = item.get('location', {}).get('name', '')
            offices = item.get('offices', [])
            office_names = [o.get('name') for o in offices]
            
            # Combine all location signals
            all_locs = [loc_name] + office_names
            
            # Check if "New York" is in any of the location strings
            is_new_york = any("New York" in loc for loc in all_locs if loc)
            
            if not is_new_york:
                continue
            
            # 2. Extract Details
            title = item.get('title')
            full_url = item.get('absolute_url')
            
            # Construct a clean location string
            location_str = loc_name if loc_name else ", ".join(office_names)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[XTX Markets] Request failed: {e}")

    print(f"[XTX Markets] Total New York jobs found: {len(jobs)}")
    return jobs

def scrape_generic(url: str) -> List[Dict[str, str]]:
    """
    Generic/fallback scraper for companies without specific implementations.
    
    """
    print(f"[Generic] No specific scraper found, attempting generic scrape: {url}")
    
    return []

def send_notification(company_name: str, new_jobs: List[Dict[str, str]]) -> None:
    """
    Sends SNS notification for new job postings.
    """
    if not SNS_TOPIC_ARN:
        print("Warning: SNS_TOPIC_ARN not configured, skipping notification")
        return
    
    # Format job list
    job_list = "\n".join([f"• {job['title']}\n  {job['url']}\n  {job['location']}" for job in new_jobs])
    
    message = f"""
    🚨 New Job Postings Found!

    Company: {company_name}
    New Positions: {len(new_jobs)}

    {job_list}

    ---
    Discovered at: {datetime.utcnow().isoformat()} UTC
    """.strip()
    
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject=f'🆕 {len(new_jobs)} New Job(s) at {company_name}'
    )