from typing import List, Dict, Any
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote

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

