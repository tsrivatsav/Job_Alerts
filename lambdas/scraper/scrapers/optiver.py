from typing import List, Dict, Any
import requests
import re

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

