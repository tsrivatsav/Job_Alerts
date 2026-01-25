from typing import List, Dict, Set, Optional
import requests

ALLOWED_DEPARTMENTS: Set[str] = {
    "Data Engineering",
    "Data Science",
    "Engineering",
    "Engineering - Backend",
    "Engineering - Data",
    "Engineering - Infrastructure",
    "Machine Learning",
}

DEPT_META_KEY = "Careersite Department (for job postings)"


def _get_metadata_value(job: Dict, key: str) -> str:
    for m in (job.get("metadata") or []):
        if m.get("name") == key:
            v = m.get("value")
            return "" if v is None else str(v).strip()
    return ""


def scrape_coinbase(
    url: str = "https://www.coinbase.com/careers/jobs",
    board_id: str = "coinbase",
    allowed_departments: Set[str] = ALLOWED_DEPARTMENTS,
    allowed_locations: Optional[Set[str]] = {"Remote - USA"},  # e.g. {"Remote - USA"}
) -> List[Dict[str, str]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_id}/jobs"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    jobs = resp.json().get("jobs", [])
    out: List[Dict[str, str]] = []

    for j in jobs:
        # Location
        loc = j.get("location") or {}
        location = (loc.get("name") or "").strip()

        if allowed_locations and location not in allowed_locations:
            continue

        # Department (authoritative)
        department = _get_metadata_value(j, DEPT_META_KEY)
        if department not in allowed_departments:
            continue

        out.append(
            {
                "title": (j.get("title") or "").strip(),
                "url": (j.get("absolute_url") or "").strip(),
                "location": location          # e.g. "Remote - USA"
            }
        )

    # De-dupe by URL
    return list({x["url"]: x for x in out if x.get("url")}.values())