"""Direct company career-page boards. Public per-company JSON APIs — no login, no scraping ToS risk.

Add company slugs to config/preferences.yaml under ats_boards.{greenhouse,lever,ashby}.
Slugs are the identifier in the company's public job board URL, e.g.
https://boards.greenhouse.io/<slug>, https://jobs.lever.co/<slug>, https://jobs.ashbyhq.com/<slug>
"""
import requests

from src.text_utils import strip_html


def fetch_greenhouse(slug):
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    resp = requests.get(url, params={"content": "true"}, timeout=30)
    resp.raise_for_status()
    return [
        {
            "id": f"greenhouse-{slug}-{job['id']}",
            "title": job["title"],
            "company": slug,
            "location": job.get("location", {}).get("name", ""),
            "url": job["absolute_url"],
            "description": strip_html(job.get("content", "")),
            "source": "greenhouse",
            "posted_at": job.get("updated_at"),
        }
        for job in resp.json().get("jobs", [])
    ]


def fetch_lever(slug):
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return [
        {
            "id": f"lever-{slug}-{job['id']}",
            "title": job["text"],
            "company": slug,
            "location": job.get("categories", {}).get("location", ""),
            "url": job["hostedUrl"],
            "description": job.get("descriptionPlain", ""),
            "source": "lever",
            "posted_at": None,
        }
        for job in resp.json()
    ]


def fetch_ashby(slug):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return [
        {
            "id": f"ashby-{slug}-{job['id']}",
            "title": job["title"],
            "company": slug,
            "location": job.get("location", ""),
            "url": job["jobUrl"],
            "description": job.get("descriptionPlain", ""),
            "source": "ashby",
            "posted_at": job.get("publishedAt"),
        }
        for job in resp.json().get("jobs", [])
    ]


def fetch(ats_config):
    jobs = []
    fetchers = [
        (ats_config.get("greenhouse", []), fetch_greenhouse),
        (ats_config.get("lever", []), fetch_lever),
        (ats_config.get("ashby", []), fetch_ashby),
    ]
    for slugs, fetcher in fetchers:
        for slug in slugs:
            try:
                jobs.extend(fetcher(slug))
            except requests.RequestException as e:
                print(f"Skipping {fetcher.__name__} slug '{slug}': {e}")
    return jobs
