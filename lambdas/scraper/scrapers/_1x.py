from typing import List, Dict, Set
import re
import requests
from bs4 import BeautifulSoup


def scrape_1x(
    url: str = "https://www.1x.tech/careers",
    allowed_headings: Set[str] = {"Artificial Intelligence (AI)", "Software Engineering"},
) -> List[Dict[str, str]]:
    """
    Scrape 1X jobs from the 1X careers page HTML, filtered to specific headings.

    Returns: [{"title":..., "url":..., "location":..., "department":...}, ...]
    """
    print(f"1X Scraping: {url}")
    print(f"Filtering headings: {sorted(allowed_headings)}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        print(f"Error: Status {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    jobs: List[Dict[str, str]] = []

    for h3 in soup.find_all("h3"):
        dept = h3.get_text(" ", strip=True)
        if dept not in allowed_headings:
            continue

        parent = h3.parent
        if not parent:
            continue

        for a in parent.find_all("a", href=True):
            href = a["href"].strip()
            if "1x.recruitee.com/o/" not in href:
                continue

            h6s = a.find_all("h6")
            if not h6s:
                continue

            title = h6s[0].get_text(" ", strip=True)

            loc_tag = a.find("h6", class_=lambda c: c and "text-gammaGrey/60" in c)
            if loc_tag:
                location = loc_tag.get_text(" ", strip=True)
            elif len(h6s) > 1:
                location = h6s[1].get_text(" ", strip=True)
            else:
                location = ""

            location = re.sub(r"\s*,\s*", ", ", location).strip()

            jobs.append(
                {
                    "title": title,
                    "url": href,
                    "location": location,
                    "department": dept,
                }
            )

    # De-dupe by URL
    deduped = {j["url"]: j for j in jobs}
    jobs = list(deduped.values())

    print(f"[1X] Found {len(jobs)} jobs (filtered)")
    return jobs
