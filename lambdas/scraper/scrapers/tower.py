from typing import List, Dict, Any
import requests

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

