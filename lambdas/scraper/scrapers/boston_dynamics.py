from typing import List, Dict
import requests
from urllib.parse import urlparse, parse_qs
import time


def scrape_boston_dynamics(url: str) -> List[Dict[str, str]]:
    """
    Scraper for Boston Dynamics (Workday).

    Uses Workday CXS endpoint:
      https://bostondynamics.wd1.myworkdayjobs.com/wday/cxs/bostondynamics/Boston_Dynamics/jobs

    Pagination: loops offsets until no new unique jobs are found.
    Also supports filters passed in the URL query string (e.g. timeType, jobFamily).
    """
    print(f"[Boston Dynamics] Scraping: {url}")

    session = requests.Session()

    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    # Workday tenant is the subdomain segment before ".wd*.myworkdayjobs.com"
    # For bostondynamics.wd1.myworkdayjobs.com => tenant="bostondynamics"
    tenant = netloc.split(".")[0]

    # Site name is the first path segment on the public board URL:
    # https://.../Boston_Dynamics/...
    path_parts = [p for p in parsed_url.path.split("/") if p]
    site_name = path_parts[0] if path_parts else "Boston_Dynamics"

    api_url = f"https://{netloc}/wday/cxs/{tenant}/{site_name}/jobs"

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "Content-Type": "application/json",
        "Origin": f"https://{netloc}",
        "Referer": url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })

    # Optional: prime session cookies + CSRF token (some Workday configs require it)
    try:
        session.get(f"https://{netloc}/{site_name}/", timeout=20)
        csrf = session.cookies.get("CALYPSO_CSRF_TOKEN")
        if csrf:
            session.headers["x-calypso-csrf-token"] = csrf
    except Exception:
        pass

    # Extract filters from query params
    query_params = parse_qs(parsed_url.query)
    search_text = query_params.get("q", [""])[0] or query_params.get("searchText", [""])[0]
    current_offset = int(query_params.get("offset", ["0"])[0])
    limit = int(query_params.get("limit", ["20"])[0])

    applied_facets = {}
    ignored_params = {"q", "searchText", "offset", "limit"}
    for k, v in query_params.items():
        if k not in ignored_params:
            applied_facets[k] = v  # keep as list, as Workday expects arrays

    jobs: List[Dict[str, str]] = []
    seen_urls = set()
    total_available = None

    max_pages = 50
    pages_fetched = 0

    while pages_fetched < max_pages:
        print(f"[Boston Dynamics] Fetching offset {current_offset}...")

        payload = {
            "appliedFacets": applied_facets,
            "limit": limit,
            "offset": current_offset,
            "searchText": search_text,
        }

        try:
            r = session.post(api_url, json=payload, timeout=30)
            if r.status_code != 200:
                print(f"[Boston Dynamics] API Error {r.status_code}")
                break

            data = r.json()
            postings = data.get("jobPostings", []) or []

            if total_available is None:
                total_available = data.get("total", 0)
                print(f"[Boston Dynamics] Total jobs available: {total_available}")

            if not postings:
                print("[Boston Dynamics] No more jobs returned (empty list). Stopping.")
                break

            new_jobs_count = 0

            for post in postings:
                title = post.get("title") or ""
                external_path = post.get("externalPath") or ""
                location = post.get("locationsText") or ""

                # Workday job URL format:
                # https://{host}/{site_name}{externalPath}
                full_url = f"https://{netloc}/{site_name}{external_path}"

                if full_url in seen_urls:
                    continue

                seen_urls.add(full_url)
                new_jobs_count += 1

                # Often requisition is in bulletFields[0], e.g. "R2192"
                req_id = ""
                bullet_fields = post.get("bulletFields") or []
                if bullet_fields:
                    req_id = bullet_fields[0] or ""

                jobs.append({
                    "title": title,
                    "url": full_url,
                    "location": location,
                    "req_id": req_id,
                })

            print(
                f"[Boston Dynamics] Page returned {len(postings)} jobs, "
                f"{new_jobs_count} new (Total: {len(jobs)}/{total_available})"
            )

            if new_jobs_count == 0:
                print("[Boston Dynamics] No new unique jobs found. Stopping.")
                break

            if len(postings) < limit:
                print(f"[Boston Dynamics] Reached last page (got {len(postings)} items).")
                break

            if total_available is not None and len(jobs) >= total_available:
                print(f"[Boston Dynamics] Collected all {total_available} available jobs.")
                break

            current_offset += limit
            pages_fetched += 1
            time.sleep(1)

        except Exception as e:
            print(f"[Boston Dynamics] Request failed: {e}")
            break

    print(f"[Boston Dynamics] Total jobs scraped: {len(jobs)}")
    return jobs


