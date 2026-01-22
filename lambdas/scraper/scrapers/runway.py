from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_runway(
    url: str = (
        "https://job-boards.greenhouse.io/runwayml"
        "?departments%5B%5D=4010359005&departments%5B%5D=4142366005&departments%5B%5D=4011161005"
    ),
) -> List[Dict[str, str]]:
    """
    Runway (Greenhouse job board HTML) scraper, using the same <tr class="job-post"> logic
    as the Phaidra/Thinking Machines example.

    Returns: [{"title":..., "url":..., "location":...}, ...]
    """
    print(f"Runway Scraping: {url}")

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

    for row in soup.find_all("tr", class_="job-post"):
        try:
            link = row.find("a", href=True)
            if not link:
                continue

            title_elem = link.find("p", class_=lambda c: c and "body--medium" in c)
            if not title_elem:
                continue
            title = title_elem.get_text(" ", strip=True)

            href = link["href"].strip()
            full_url = href if href.startswith("http") else urljoin("https://job-boards.greenhouse.io/", href)

            location = ""
            loc_elem = link.find("p", class_=lambda c: c and "body--metadata" in c)
            if loc_elem:
                location = loc_elem.get_text(" ", strip=True)

            jobs.append({"title": title, "url": full_url, "location": location})
        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue

    # de-dupe by URL
    jobs = list({j["url"]: j for j in jobs}.values())

    print(f"[Runway] Found {len(jobs)} jobs")
    return jobs

