"""RemoteOK public JSON API.

Note: Wellfound (AngelList Talent) deprecated its public jobs API years ago and
scraping its logged-in search UI carries the same ToS risk as LinkedIn, so it's
skipped. RemoteOK's /api endpoint is public and documented for this use case.
"""
import requests

from src.text_utils import strip_html

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "job-agent/1.0 (personal job search tool)"}


def fetch():
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    entries = resp.json()
    jobs = []
    for job in entries:
        if "id" not in job:
            continue  # first element is a legal notice, not a job
        tags = [t.lower() for t in job.get("tags", [])]
        if not any(t in tags for t in ("frontend", "react", "javascript", "vue", "typescript")):
            continue
        jobs.append({
            "id": f"remoteok-{job['id']}",
            "title": job.get("position", ""),
            "company": job.get("company", ""),
            "location": job.get("location", "Remote"),
            "url": job.get("url", ""),
            "description": strip_html(job.get("description", "")),
            "source": "remoteok",
            "posted_at": job.get("date"),
        })
    return jobs
