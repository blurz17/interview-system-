"""
Job Specification Fetcher
Fetches and structures job specifications from LinkedIn public guest API, generic URLs, or raw text.
Uses httpx and BeautifulSoup.
"""

import re
import httpx
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_linkedin_job_id(url: str) -> Optional[str]:
    match = re.search(r"/view/(\d+)", url) or re.search(r"currentJobId=(\d+)", url) or re.search(r"/(\d{8,})", url)
    return match.group(1) if match else None


def fetch_job_from_url(url: str) -> Dict[str, Any]:
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("Invalid URL format.")

    with httpx.Client(headers=HEADERS, timeout=15.0, follow_redirects=True) as client:
        # 1. LinkedIn URL handler
        if "linkedin.com" in url:
            job_id = extract_linkedin_job_id(url)
            if job_id:
                guest_api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
                try:
                    resp = client.get(guest_api_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        title_elem = soup.find("h2", class_="top-card-layout__title") or soup.find("h1") or soup.find("h2")
                        title = title_elem.get_text(strip=True) if title_elem else "Backend Engineer"

                        company_elem = soup.find("a", class_="topcard__org-name-link") or soup.find("span", class_="topcard__flavor")
                        company = company_elem.get_text(strip=True) if company_elem else "Employer"

                        loc_elem = soup.find("span", class_="topcard__flavor--bullet")
                        location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"

                        desc_elem = soup.find("div", class_="show-more-less-html__markup") or soup.find("section", class_="show-more-less-html")
                        desc = desc_elem.get_text("\n", strip=True) if desc_elem else resp.text

                        return {
                            "source": "linkedin_guest_api",
                            "title": title,
                            "company": company,
                            "location": location,
                            "description": desc,
                            "url": url,
                        }
                except Exception:
                    pass

            # Fallback to direct page request
            resp = client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title_elem = soup.find("h1") or soup.find("h2")
            title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
            company_elem = soup.find("a", class_="topcard__org-name-link") or soup.find("span", class_="topcard__flavor")
            company = company_elem.get_text(strip=True) if company_elem else "Company"
            loc_elem = soup.find("span", class_="topcard__flavor--bullet")
            location = loc_elem.get_text(strip=True) if loc_elem else "Not specified"
            desc_elem = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="description__text")
            desc = desc_elem.get_text("\n", strip=True) if desc_elem else soup.get_text("\n", strip=True)
            return {
                "source": "linkedin_direct",
                "title": title,
                "company": company,
                "location": location,
                "description": desc,
                "url": url,
            }

        # 2. Generic web portal
        resp = client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for s in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            s.extract()
        title_elem = soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Job Position"
        main_elem = soup.find("article") or soup.find("main") or soup.body
        desc = main_elem.get_text("\n", strip=True) if main_elem else soup.get_text("\n", strip=True)
        return {
            "source": "generic_web",
            "title": title,
            "company": "External Employer",
            "location": "Not specified",
            "description": desc,
            "url": url,
        }
