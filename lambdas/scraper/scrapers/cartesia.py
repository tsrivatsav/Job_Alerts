from typing import List, Dict
import requests

def scrape_cartesia(url: str = "https://jobs.ashbyhq.com/cartesia") -> List[Dict[str, str]]:
    """
    Scrapes Cartesia jobs via AshbyHQ GraphQL API (jobBoardWithTeams).
    Uses the same flat-list strategy: Teams and JobPostings are siblings.
    """
    print(f"Cartesia Scraping: {url}")

    # 1. Extract organization slug
    # Based on Ashby URL pattern, the org page slug is the last path segment.
    if "cartesia" in url:
        org_name = "cartesia"
    else:
        org_name = url.rstrip("/").split("/")[-1]

    # 2. Setup API
    api_url = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "apollographql-client-name": "frontend_non_user",
        "apollographql-client-version": "0.1.0",
    }

    # 3. GraphQL query (same as Liquid AI)
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
        "variables": {"organizationHostedJobsPageName": org_name},
        "query": query,
    }

    jobs: List[Dict[str, str]] = []

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"Error: Status {resp.status_code}")
            return []

        data = resp.json()

        job_board = data.get("data", {}).get("jobBoard", {})
        if not job_board:
            print("No job board data returned.")
            return []

        postings = job_board.get("jobPostings", []) or []

        for post in postings:
            job_id = post.get("id")
            title = post.get("title") or ""
            if not job_id:
                continue

            # Canonical Ashby job URL
            full_url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"

            # Location(s)
            locs = []
            if post.get("locationName"):
                locs.append(post["locationName"])
            for sec in post.get("secondaryLocations", []) or []:
                if sec.get("locationName"):
                    locs.append(sec["locationName"])
            location_str = ", ".join(dict.fromkeys(locs))  # de-dupe, preserve order

            jobs.append(
                {
                    "title": title,
                    "url": full_url,
                    "location": location_str,
                    # Optional extras if you want them:
                    # "workplaceType": post.get("workplaceType") or "",
                    # "employmentType": post.get("employmentType") or "",
                }
            )

    except Exception as e:
        print(f"Error scraping Cartesia: {e}")
        return []

    print(f"[Cartesia] Found {len(jobs)} jobs")
    return jobs
