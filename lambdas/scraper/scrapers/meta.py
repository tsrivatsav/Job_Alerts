import json
from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import time
import re

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

