import json
from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import ast

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
