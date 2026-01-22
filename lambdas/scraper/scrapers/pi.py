from typing import List, Dict, Any
import requests

def scrape_pi(url: str = "https://jobs.ashbyhq.com/physicalintelligence") -> List[Dict[str, str]]:
    """
    Physical Intelligence (PI) scraping logic via AshbyHQ GraphQL API.
    Derived from the JS snippet provided which identifies the org as 'physicalintelligence'.
    """
    print(f"Physical Intelligence Scraping: {url}")
    
    # 1. Extract the organization name
    # The JS snippet explicitly defines: window.__ashbyBaseJobBoardUrl = "https://jobs.ashbyhq.com/physicalintelligence"
    # Therefore, the organization slug is 'physicalintelligence'.
    if "physicalintelligence" in url:
        org_name = "physicalintelligence"
    else:
        # Fallback if a different URL structure is passed
        org_name = url.rstrip('/').split('/')[-1]
    
    # 2. Setup the GraphQL endpoint and headers
    # Ashby uses a shared API endpoint for all public job boards
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'Accept': '*/*'
    }
    
    # 3. Define the GraphQL query
    # This query retrieves job postings, titles, and locations
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
            # Standard Ashby URL pattern
            full_url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"
            
            # Format location (Primary + Secondaries)
            locs = [post.get('locationName')]
            secondaries = post.get('secondaryLocations', [])
            if secondaries:
                for sec in secondaries:
                    if sec.get('locationName'):
                        locs.append(sec.get('locationName'))
            
            # Filter out None/Empty values and join
            location_str = ", ".join([l for l in locs if l])
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"Error fetching/parsing GraphQL data for Physical Intelligence: {e}")

    print(f"[Physical Intelligence] Found {len(jobs)} jobs")
    return jobs
