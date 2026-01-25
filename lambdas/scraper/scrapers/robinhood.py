from typing import List, Dict, Set
import requests


def _get_metadata_value(job: Dict, key: str) -> str:
    for m in (job.get("metadata") or []):
        if m.get("name") == key:
            v = m.get("value")
            return "" if v is None else str(v).strip()
    return ""


def scrape_robinhood(
    url: str = "https://api.greenhouse.io/v1/boards/robinhood/jobs",
    allowed_bucket: str = "ENGINEERING & SECURITY",
    allowed_locations: Set[str] = {
        "Bellevue, WA",
        "Chicago, IL",
        "Denver, CO",
        "Lake Mary, FL",
        "Menlo Park, CA",
        "New York, NY",
        "Washington, DC",
        "Westlake, TX",
    },
) -> List[Dict[str, str]]:
    """
    Scrapes Robinhood jobs from Greenhouse Job Board API, filtered to:
      - metadata["Careers Page Bucket"] == "ENGINEERING & SECURITY"
      - location.name in allowed_locations

    Returns: [{"title":..., "url":..., "location":...}, ...]
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,*/*",
        "Origin": "https://careers.robinhood.com",
        "Referer": "https://careers.robinhood.com/",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    jobs = resp.json().get("jobs", [])
    out: List[Dict[str, str]] = []

    for j in jobs:
        bucket = _get_metadata_value(j, "Careers Page Bucket")
        if bucket != allowed_bucket:
            continue

        loc_obj = j.get("location") or {}
        location = (loc_obj.get("name") or "").strip()
        if location not in allowed_locations:
            continue

        out.append(
            {
                "title": (j.get("title") or "").strip(),
                "url": (j.get("absolute_url") or "").strip(),
                "location": location,
            }
        )

    # De-dupe by URL
    out = list({x["url"]: x for x in out if x.get("url")}.values())
    print(f"Robinhood: found {len(out)} jobs")
    return out
