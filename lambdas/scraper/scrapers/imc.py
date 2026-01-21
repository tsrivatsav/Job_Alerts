import json
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time
import re
import curl_cffi

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

