from typing import List, Dict, Any
import requests

def scrape_liquid(url: str = "https://jobs.ashbyhq.com/liquid-ai") -> List[Dict[str, str]]:
    """
    Scrapes Liquid AI jobs via AshbyHQ GraphQL API.
    Adapts the flat-list strategy where Teams and JobPostings are siblings in the response.
    """
    print(f"Liquid AI Scraping: {url}")
    
    # 1. Extract organization name
    # Based on the network logs provided, the slug is 'liquid-ai'
    if "liquid-ai" in url:
        org_name = "liquid-ai"
    else:
        org_name = url.rstrip('/').split('/')[-1]
    
    # 2. Setup API
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
    }
    
    # 3. Exact GraphQL Query from your Liquid AI network inspection
    query = """
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
            "organizationHostedJobsPageName": org_name
        },
        "query": query
    }
    
    jobs = []
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error: Status {response.status_code}")
            return []

        data = response.json()
        
        # 4. Parse Data
        job_board = data.get('data', {}).get('jobBoard', {})
        if not job_board:
            print("No job board data returned.")
            return []

        # B. Process Job Postings
        postings = job_board.get('jobPostings', [])
        
        for post in postings:
            title = post.get('title')
            job_id = post.get('id')
            
            # Construct URL
            full_url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"
            
            # Resolve Locations
            locs = []
            if post.get('locationName'):
                locs.append(post.get('locationName'))
            
            # Add secondary locations
            for sec in post.get('secondaryLocations', []):
                if sec.get('locationName'):
                    locs.append(sec.get('locationName'))
            
            location_str = ", ".join(locs)

            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"Error scraping Liquid AI: {e}")

    print(f"[Liquid AI] Found {len(jobs)} jobs")
    return jobs
