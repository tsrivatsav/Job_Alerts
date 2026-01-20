from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import cloudscraper
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin, unquote
import html
import json
import re
import time
import ast
import curl_cffi

def scrape_reflectionai(url: str = "https://jobs.ashbyhq.com/reflectionai") -> List[Dict[str, str]]:
    print(f"[ReflectionAI] Scraping: {url}")
    
    # 1. Setup Session
    # Ashby uses Cloudflare, so impersonating Chrome is safer.
    session = curl_cffi.requests.Session(impersonate="chrome120")
    
    # 2. Define API Endpoint and Headers
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    
    headers = {
        'content-type': 'application/json',
        'apollographql-client-name': 'frontend_non_user',
        'apollographql-client-version': '0.1.0',
        'accept': '*/*',
        'origin': 'https://jobs.ashbyhq.com',
        'referer': 'https://jobs.ashbyhq.com/reflectionai',
    }
    
    # 3. Define the GraphQL Payload
    # This matches exactly what you saw in the Network tab.
    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {
            "organizationHostedJobsPageName": "reflectionai"
        },
        "query": """query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
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
    }

    all_jobs = []

    try:
        # 4. Make the POST Request
        response = session.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[ReflectionAI] API Error: {response.status_code}")
            print(response.text)
            return []
            
        data = response.json()
        
        # 5. Extract Data
        # Structure: data -> data -> jobBoard -> jobPostings
        job_list = data.get('data', {}).get('jobBoard', {}).get('jobPostings', [])
        
        print(f"[ReflectionAI] Found {len(job_list)} jobs.")
        
        for job in job_list:
            j_id = job.get('id')
            title = job.get('title')
            
            # Construct URL
            # Ashby URLs are standard: base_url + /job_id
            full_url = f"https://jobs.ashbyhq.com/reflectionai/{j_id}"
            
            # Handle Locations (Primary + Secondary)
            locations = []
            if job.get('locationName'):
                locations.append(job.get('locationName'))
                
            for sec in job.get('secondaryLocations', []):
                sec_name = sec.get('locationName')
                if sec_name and sec_name not in locations:
                    locations.append(sec_name)
            
            location_str = ", ".join(locations)
            
            all_jobs.append({
                'title': title,
                'url': full_url,
                'location': location_str
            })
            
    except Exception as e:
        print(f"[ReflectionAI] Request failed: {e}")

    print(f"[ReflectionAI] Total jobs collected: {len(all_jobs)}")
    return all_jobs

print(scrape_reflectionai("https://jobs.ashbyhq.com/reflectionai")[:5])