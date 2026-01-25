from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_world_labs(url: str = "https://job-boards.greenhouse.io/worldlabs") -> List[Dict[str, str]]:
    """
    Scrapes World Labs Greenhouse job board HTML.

    Expected row structure:
      <tr class="job-post">
        <td class="cell">
          <a href="...">
            <p class="body body--medium">TITLE</p>
            <p class="body body__secondary body--metadata">LOCATION</p>
          </a>
        </td>
      </tr>

    Returns:
      [{"title":..., "url":..., "location":...}, ...]
    """
    print(f"World Labs Scraping: {url}")

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

    for row in soup.select("tr.job-post"):
        link = row.find("a", href=True)
        if not link:
            continue

        title_elem = link.find("p", class_=lambda c: c and "body--medium" in c)
        if not title_elem:
            continue

        title = next(iter(title_elem.stripped_strings), "").strip()
        if not title:
            continue

        href = link["href"].strip()
        full_url = href if href.startswith("http") else urljoin(url, href)

        loc_elem = link.find("p", class_=lambda c: c and "body--metadata" in c)
        location = loc_elem.get_text(" ", strip=True) if loc_elem else ""

        jobs.append({"title": title, "url": full_url, "location": location})

    # de-dupe by URL
    jobs = list({j["url"]: j for j in jobs if j.get("url")}.values())

    print(f"[World Labs] Found {len(jobs)} jobs")
    return jobs
