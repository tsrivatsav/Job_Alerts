from typing import List, Dict, Any
import requests

def scrape_openai(url: str) -> List[Dict[str, str]]:
    """
    OpenAI (Ashby) scraping logic via GraphQL API.
    Filters by specific teams and locations.
    """
    print(f"[OpenAI] Scraping: {url}")
    
    # 1. Extract the organization name from the URL
    org_name = url.rstrip('/').split('/')[-1]
    if '?' in org_name:
        org_name = org_name.split('?')[0]
    
    # 2. Define filters
    ALLOWED_TEAMS = {
        'Applied AI Infrastructure',
        'Alignment',
        'Foundations',
        'Human Data',
        'OpenAI Labs',
        'Post-training',
        'Reasoning',
        'Robotics',
        'Sora',
        'Training'
    }
    
    ALLOWED_LOCATIONS = {
        'Washington, DC',
        'San Francisco',
        'Remote - US',
        'New York City',
        'Seattle'
    }
    
    # 3. Setup the GraphQL endpoint and headers
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'Origin': 'https://jobs.ashbyhq.com',
        'Referer': f'https://jobs.ashbyhq.com/{org_name}',
        'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    # 4. Define the GraphQL query
    query = """query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
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
}"""
    
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
        job_board = data.get('data', {}).get('jobBoard', {})
        postings = job_board.get('jobPostings', [])
        teams = job_board.get('teams', [])
        
        # Build simple team lookup: id -> name
        team_lookup = {}
        for team in teams:
            team_id = team['id']
            # Use externalName if available, otherwise name
            team_name = team.get('externalName') or team.get('name')
            team_lookup[team_id] = team_name
        
        def get_all_locations(post: dict) -> List[str]:
            """Get primary + secondary locations"""
            locations = []
            if post.get('locationName'):
                locations.append(post.get('locationName'))
            
            for sec in post.get('secondaryLocations', []):
                if sec.get('locationName'):
                    locations.append(sec.get('locationName'))
            
            return locations
        
        def matches_allowed_location(locations: List[str]) -> bool:
            """Check if any location matches allowed list"""
            for loc in locations:
                if loc in ALLOWED_LOCATIONS:
                    return True
            return False
        
        for post in postings:
            team_id = post.get('teamId')
            team_name = team_lookup.get(team_id, 'Unknown')
            
            # Check team filter - only look at the team itself, not parents
            if team_name not in ALLOWED_TEAMS:
                continue
            
            # Check location filter
            locations = get_all_locations(post)
            if not matches_allowed_location(locations):
                continue
            
            # Build job entry
            title = post.get('title')
            job_id = post.get('id')
            full_url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"
            
            # Filter locations to only show allowed ones
            filtered_locations = [loc for loc in locations if loc in ALLOWED_LOCATIONS]
            location_str = ", ".join(filtered_locations) if filtered_locations else ", ".join(locations)
            
            jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[OpenAI] Error fetching/parsing GraphQL data: {e}")
        

    print(f"[OpenAI] Found {len(jobs)} jobs matching filters")
    return jobs
