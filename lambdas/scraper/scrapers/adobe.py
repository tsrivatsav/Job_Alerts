from typing import List, Dict, Any, Optional
import base64
import json
import time
import requests


def _extract_csrf_from_play_session(cookie_val: str) -> str:
    parts = cookie_val.split(".")
    if len(parts) < 2:
        return ""
    payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
    payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
    payload = json.loads(payload_json)
    return (payload.get("data") or {}).get("csrfToken", "") or ""


def scrape_adobe(
    url: str = "https://careers.adobe.com/widgets",
    sleep_s: float = 0.2,
    max_pages: Optional[int] = None,  # safety valve
) -> List[Dict[str, str]]:
    session = requests.Session()

    referer = "https://careers.adobe.com/us/en/c/research-jobs"
    session.get(referer, timeout=30)

    csrf_token = ""
    if "PLAY_SESSION" in session.cookies:
        csrf_token = _extract_csrf_from_play_session(session.cookies.get("PLAY_SESSION", ""))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://careers.adobe.com",
        "Referer": referer,
    }
    if csrf_token:
        headers["x-csrf-token"] = csrf_token

    base_payload: Dict[str, Any] = {
        "lang": "en_us",
        "deviceType": "desktop",
        "country": "us",
        "pageName": "Research jobs",
        "ddoKey": "refineSearch",
        "sortBy": "Most recent",
        "subsearch": "machine%20learning",
        "from": 0,                 # will be changed in loop
        "jobs": True,
        "counts": True,
        "all_fields": [
            "remote", "country", "state", "city", "experienceLevel",
            "category", "profession", "employmentType", "jobLevel",
        ],
        "pageType": "category",
        "size": 10,                # page size; can increase if Adobe accepts it
        "rk": "",
        "ak": "",
        "clearAll": False,
        "jdsource": "facets",
        "isSliderEnable": False,
        "pageId": "page66-ds",
        "siteType": "external",
        "location": "",
        "keywords": "",
        "global": True,
        "selected_fields": {
            "country": ["United States of America"],
            "experienceLevel": ["Experienced"],
            "category": ["Research", "Engineering and Product"],
            "profession": [
                "Analytics & Data Science",
                "Engineering",
                "Applied Science",
                "Research",
                "Software Development Engineering",
            ],
            "employmentType": ["Full time"],
            "jobLevel": ["Individual Contributor"],
        },
        "sort": {"order": "desc", "field": "postedDate"},
        "locationData": {},
    }

    size = int(base_payload["size"])
    offset = 0
    page = 0
    total_hits: Optional[int] = None

    results: List[Dict[str, str]] = []

    while True:
        page += 1
        if max_pages is not None and page > max_pages:
            break

        payload = dict(base_payload)
        payload["from"] = offset

        resp = session.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        refine = data.get("refineSearch") or {}
        total_hits = total_hits if total_hits is not None else refine.get("totalHits")

        jobs = (((refine.get("data") or {}).get("jobs")) or [])
        if not jobs:
            break

        for j in jobs:
            results.append(
                {
                    "title": (j.get("title") or "").strip(),
                    "url": (j.get("applyUrl") or "").strip(),
                    "location": (j.get("location") or "").strip(),
                }
            )

        # stop conditions
        offset += size
        if total_hits is not None and offset >= int(total_hits):
            break
        if len(jobs) < size:
            break

        time.sleep(sleep_s)

    # De-dupe by URL
    results = list({x["url"]: x for x in results if x.get("url")}.values())
    print(f"Scraped {len(results)} Adobe jobs.")
    return results

