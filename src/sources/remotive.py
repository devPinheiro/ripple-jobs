"""Remotive public API — no key required. https://remotive.com/api-documentation

The API's `search` param doesn't actually filter results (verified: it returns the full
category regardless of the term), so this fetches the whole software-dev category and
leaves relevance filtering to the scorer.
"""
import requests

API_URL = "https://remotive.com/api/remote-jobs"


def fetch():
    resp = requests.get(API_URL, params={"category": "software-dev"}, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [
        {
            "id": f"remotive-{job['id']}",
            "title": job["title"],
            "company": job["company_name"],
            "location": job.get("candidate_required_location", ""),
            "url": job["url"],
            "description": job.get("description", ""),
            "source": "remotive",
            "posted_at": job.get("publication_date"),
        }
        for job in jobs
    ]
