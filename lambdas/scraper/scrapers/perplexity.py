from typing import List, Dict, Any
import requests

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

