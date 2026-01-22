from typing import List, Dict, Any, Set
import requests


def scrape_suno(
    url: str = "https://jobs.ashbyhq.com/suno",
    allowed_teams: Set[str] = {"Data", "Engineering", "Machine Learning"},
) -> List[Dict[str, str]]:
    """
    Scrapes Suno jobs via AshbyHQ GraphQL API (jobBoardWithTeams),
    filtering to postings whose team name is in allowed_teams.

    Returns: [{"title":..., "url":..., "location":..., "team":...}, ...]
    """
    print(f"Suno Scraping: {url}")
    print(f"Filtering teams: {sorted(allowed_teams)}")

    # org slug
    org_name = url.rstrip("/").split("/")[-1]  # "suno"

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

    payload: Dict[str, Any] = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {"organizationHostedJobsPageName": org_name},
        "query": query,
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"Error: Status {resp.status_code}")
            return []

        data = resp.json()
        job_board = data.get("data", {}).get("jobBoard", {})
        if not job_board:
            print("No job board data returned.")
            return []

        teams = job_board.get("teams", []) or []
        postings = job_board.get("jobPostings", []) or []

        # Map teamId -> team name (use externalName if present, else name)
        team_id_to_name: Dict[str, str] = {}
        for t in teams:
            tid = t.get("id")
            if not tid:
                continue
            team_name = t.get("externalName") or t.get("name") or ""
            team_id_to_name[tid] = team_name

        jobs: List[Dict[str, str]] = []

        for post in postings:
            job_id = post.get("id")
            if not job_id:
                continue

            team_name = team_id_to_name.get(post.get("teamId", ""), "")
            if team_name not in allowed_teams:
                continue

            # Locations (primary + secondary)
            locs = []
            if post.get("locationName"):
                locs.append(post["locationName"])
            for sec in (post.get("secondaryLocations") or []):
                if sec.get("locationName"):
                    locs.append(sec["locationName"])
            location = ", ".join(dict.fromkeys(locs))  # de-dupe, preserve order

            jobs.append(
                {
                    "title": post.get("title") or "",
                    "url": f"https://jobs.ashbyhq.com/{org_name}/{job_id}",
                    "location": location
                }
            )

        print(f"[Suno] Found {len(jobs)} jobs (filtered)")
        return jobs

    except Exception as e:
        print(f"Error scraping Suno: {e}")
        return []