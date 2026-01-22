from typing import List, Dict, Any, Set
import requests


def scrape_luma(
    url: str = "https://jobs.gem.com/lumalabs-ai",
    allowed_departments: Set[str] = {
        "Applied Research & Engineering",
        "Backend Platforms",
        "Data Infrastructure",
        "ML Engineering",
        "Operations",
        "Research",
    },
) -> List[Dict[str, str]]:
    """
    Scrapes Luma jobs from Gem's public GraphQL batch endpoint, filtered by department.

    Job URL format:
      https://jobs.gem.com/<boardId>/<extId>
    """
    print(f"Luma Scraping: {url}")
    print(f"Filtering departments: {sorted(allowed_departments)}")

    board_id = url.rstrip("/").split("/")[-1]  # "lumalabs-ai"
    api_url = "https://jobs.gem.com/api/public/graphql/batch"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Accept": "*/*",
        "batch": "true",
    }

    payload: List[Dict[str, Any]] = [
        {
            "operationName": "JobBoardTheme",
            "variables": {"boardId": board_id},
            "query": """query JobBoardTheme($boardId: String!) {
              publicBrandingTheme(externalId: $boardId) {
                id
                theme
                __typename
              }
            }""",
        },
        {
            "operationName": "JobBoardList",
            "variables": {"boardId": board_id},
            "query": """query JobBoardList($boardId: String!) {
              oatsExternalJobPostings(boardId: $boardId) {
                jobPostings {
                  id
                  extId
                  title
                  locations {
                    id
                    name
                    city
                    isoCountry
                    isRemote
                    extId
                    __typename
                  }
                  job {
                    id
                    department {
                      id
                      name
                      extId
                      __typename
                    }
                    locationType
                    employmentType
                    __typename
                  }
                  __typename
                }
                __typename
              }
              oatsExternalJobPostingsFilters(boardId: $boardId) {
                type
                displayName
                rawValue
                value
                count
                __typename
              }
              jobBoardExternal(vanityUrlPath: $boardId) {
                id
                teamDisplayName
                descriptionHtml
                pageTitle
                __typename
              }
            }""",
        },
    ]

    jobs: List[Dict[str, str]] = []

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"Error: Status {resp.status_code}")
            return []

        batch = resp.json()
        if not isinstance(batch, list):
            print("Unexpected response shape (expected a list batch response).")
            return []

        job_list_item = next(
            (
                item
                for item in batch
                if isinstance(item, dict)
                and isinstance(item.get("data"), dict)
                and "oatsExternalJobPostings" in item["data"]
            ),
            None,
        )
        if not job_list_item:
            print("No JobBoardList data returned.")
            return []

        postings = (
            job_list_item.get("data", {})
            .get("oatsExternalJobPostings", {})
            .get("jobPostings", [])
        ) or []

        for post in postings:
            ext_id = post.get("extId")
            if not ext_id:
                continue

            department = ((post.get("job") or {}).get("department") or {}).get("name", "") or ""
            if department not in allowed_departments:
                continue

            title = post.get("title") or ""
            job_url = f"https://jobs.gem.com/{board_id}/{ext_id}"

            locs = []
            for loc in (post.get("locations") or []):
                if loc.get("name"):
                    locs.append(loc["name"])
            location = ", ".join(dict.fromkeys(locs))

            jobs.append(
                {
                    "title": title,
                    "url": job_url,
                    "location": location
                }
            )

    except Exception as e:
        print(f"Error scraping Luma: {e}")
        return []

    print(f"[Luma] Found {len(jobs)} jobs (filtered)")
    return jobs

    