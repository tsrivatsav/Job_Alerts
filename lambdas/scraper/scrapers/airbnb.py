from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse


def _set_paged(url: str, paged: int) -> str:
    parts = urlparse(url)
    qs = parse_qs(parts.query)
    qs["_paged"] = [str(paged)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))


def scrape_airbnb(
    url: str = "https://careers.airbnb.com/positions/?_offices=united-states&_workplace_type=live-and-work-anywhere&_jobs_sort=updated_at&_paged=1",
    max_pages: Optional[int] = None,
) -> List[Dict[str, str]]:
    """
    Scrapes Airbnb positions pages (HTML) and paginates via `_paged`.
    Stops when FacetWP pager shows 'No results' or the list is empty.

    Returns: [{"title":..., "url":..., "location":...}, ...]
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    jobs: List[Dict[str, str]] = []
    page = 1

    while True:
        if max_pages is not None and page > max_pages:
            break

        page_url = _set_paged(url, page)
        resp = requests.get(page_url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Hard stop: FacetWP pager says "No results"
        pager = soup.select_one(
            'div.facetwp-facet[data-name="jobs_pager"][data-type="pager"]'
        )
        if pager and pager.get_text(" ", strip=True).lower() == "no results":
            break

        page_jobs: List[Dict[str, str]] = []
        for li in soup.select('ul.job-list[role="list"] > li[role="listitem"]'):
            a = li.select_one("h3 a[href]")
            if not a:
                continue

            title = a.get_text(" ", strip=True)
            href = a["href"].strip()
            full_url = href if href.startswith("http") else urljoin(page_url, href)

            loc_span = li.select_one("div.flex.justify-end span")
            location = loc_span.get_text(" ", strip=True) if loc_span else ""

            if title and full_url:
                page_jobs.append({"title": title, "url": full_url, "location": location})

        # Secondary stop: empty list
        if not page_jobs:
            break

        jobs.extend(page_jobs)
        page += 1

    # de-dupe by URL
    print(f"Scraped {len(jobs)} job listings from Airbnb")
    return list({j["url"]: j for j in jobs if j.get("url")}.values())
