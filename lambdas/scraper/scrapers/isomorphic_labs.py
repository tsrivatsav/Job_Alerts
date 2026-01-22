from typing import List, Dict, Set
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_isomorphic_labs(
    url: str = "https://job-boards.greenhouse.io/isomorphiclabs",
    allowed_departments: Set[str] = {"ML Research", "Generalist Software Engineering", "ML Engineering"},
) -> List[Dict[str, str]]:
    """
    Scrapes Isomorphic Labs Greenhouse job board HTML, filtered to specific department headings.

    Page structure (as in your snippet):
      <div class="job-posts--table--department">
        <h3>DEPARTMENT NAME</h3>
        <table> ... <tr class="job-post">...</tr> ... </table>
      </div>

    Returns:
      [{"title":..., "url":..., "location":..., "department":...}, ...]
    """
    print(f"Isomorphic Labs Scraping: {url}")
    print(f"Filtering departments: {sorted(allowed_departments)}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    jobs: List[Dict[str, str]] = []

    # Iterate department blocks, only parse those whose <h3> matches allowed_departments
    for dept_block in soup.select("div.job-posts--table--department"):
        h3 = dept_block.find("h3")
        if not h3:
            continue

        dept_name = h3.get_text(" ", strip=True)
        if dept_name not in allowed_departments:
            continue

        for row in dept_block.select("tr.job-post"):
            link = row.find("a", href=True)
            if not link:
                continue

            title_elem = link.find("p", class_=lambda c: c and "body--medium" in c)
            if not title_elem:
                continue

            # Avoid "New" badge polluting the title
            title = next(iter(title_elem.stripped_strings), "").strip()
            if not title:
                continue

            href = link["href"].strip()
            full_url = href if href.startswith("http") else urljoin(url, href)

            loc_elem = link.find("p", class_=lambda c: c and "body--metadata" in c)
            location = loc_elem.get_text(" ", strip=True) if loc_elem else ""

            jobs.append(
                {
                    "title": title,
                    "url": full_url,
                    "location": location
                }
            )

    # de-dupe by URL
    jobs = list({j["url"]: j for j in jobs}.values())

    print(f"[Isomorphic Labs] Found {len(jobs)} jobs (filtered)")
    return jobs

