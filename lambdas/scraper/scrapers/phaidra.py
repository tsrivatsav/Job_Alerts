from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scrape_phaidra(url: str = "https://job-boards.greenhouse.io/phaidra") -> List[Dict[str, str]]:
    """
    Phaidra scraping logic (HTML table rows like Thinking Machines example).

    Expected row pattern:
      <tr class="job-post">
        <td class="cell">
          <a href="https://job-boards.greenhouse.io/phaidra/jobs/4647610005" ...>
            <p class="body body--medium">Title ...</p>
            <p class="body ... body--metadata">Location</p>
          </a>
        </td>
      </tr>

    Returns: [{"title":..., "url":..., "location":...}, ...]
    """
    print(f"Phaidra Scraping: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
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

            # Title is in a <p> whose class includes 'body--medium'
            title_elem = link.find("p", class_=lambda c: c and "body--medium" in c)
            if not title_elem:
                continue

            # Use .stripped_strings so "New" badge doesn't pollute the title
            title = next(iter(title_elem.stripped_strings), "").strip()
            if not title:
                continue

            href = link["href"].strip()
            full_url = href if href.startswith("http") else urljoin(url, href)

            # Location is in a <p> whose class includes 'body--metadata'
            location = ""
            loc_elem = link.find("p", class_=lambda c: c and "body--metadata" in c)
            if loc_elem:
                location = loc_elem.get_text(" ", strip=True)

            jobs.append({"title": title, "url": full_url, "location": location})

        except Exception as e:
            print(f"Error parsing job listing: {e}")
            continue

    # de-dupe by URL
    deduped = {j["url"]: j for j in jobs}
    jobs = list(deduped.values())

    print(f"[Phaidra] Found {len(jobs)} jobs")
    return jobs
