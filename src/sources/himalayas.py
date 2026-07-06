"""Himalayas public API — no auth. https://himalayas.app/docs/remote-jobs-api"""
import requests

from src.text_utils import strip_html

API_URL = "https://himalayas.app/jobs/api/search"


def fetch(query="frontend"):
    resp = requests.get(API_URL, params={"limit": 20, "q": query}, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [
        {
            "id": f"himalayas-{job['guid']}",
            "title": job.get("title", ""),
            "company": job.get("companyName", ""),
            "location": ", ".join(job.get("locationRestrictions") or []) or "Remote",
            "url": job.get("applicationLink", job.get("guid", "")),
            "description": strip_html(job.get("description") or job.get("excerpt", "")),
            "source": "himalayas",
            "posted_at": job.get("pubDate"),
        }
        for job in jobs
    ]
