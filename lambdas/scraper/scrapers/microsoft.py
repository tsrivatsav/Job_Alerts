from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time
import re
import curl_cffi

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

