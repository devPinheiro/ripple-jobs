"""Jobicy public API — no auth. https://jobicy.com/api/v2/remote-jobs

ToS note: Jobicy's docs permit personal/programmatic use but explicitly forbid
redistributing listings to competing aggregators (Google Jobs, LinkedIn, Jooble)
and ask for at most hourly polling — fine for this tool's own private use.
"""
import requests

from src.text_utils import strip_html

API_URL = "https://jobicy.com/api/v2/remote-jobs"


def fetch(tag="frontend"):
    resp = requests.get(API_URL, params={"count": 50, "tag": tag}, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [
        {
            "id": f"jobicy-{job['id']}",
            "title": job.get("jobTitle", ""),
            "company": job.get("companyName", ""),
            "location": job.get("jobGeo", "Remote"),
            "url": job.get("url", ""),
            "description": strip_html(job.get("jobDescription") or job.get("jobExcerpt", "")),
            "source": "jobicy",
            "posted_at": job.get("pubDate"),
        }
        for job in jobs
    ]
