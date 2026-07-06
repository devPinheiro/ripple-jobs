"""The Muse public API — no key needed for basic use (500 req/hr).
https://www.themuse.com/developers/api/v2
"""
import requests

from src.text_utils import strip_html

API_URL = "https://www.themuse.com/api/public/jobs"


def fetch(category="Software Engineering"):
    resp = requests.get(API_URL, params={"category": category, "page": 0}, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("results", [])
    return [
        {
            "id": f"themuse-{job['id']}",
            "title": job.get("name", ""),
            "company": job.get("company", {}).get("name", ""),
            "location": ", ".join(loc["name"] for loc in job.get("locations", [])) or "Remote",
            "url": job.get("refs", {}).get("landing_page", ""),
            "description": strip_html(job.get("contents", "")),
            "source": "themuse",
            "posted_at": job.get("publication_date"),
        }
        for job in jobs
    ]
