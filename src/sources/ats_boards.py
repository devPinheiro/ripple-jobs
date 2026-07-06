"""Direct company career-page boards. Public per-company JSON APIs — no login, no scraping ToS risk.

Add company slugs to config/preferences.yaml under ats_boards.{greenhouse,lever,ashby,workable,
recruitee,teamtailor}. Slugs are the identifier in the company's public job board URL, e.g.
https://boards.greenhouse.io/<slug>, https://jobs.lever.co/<slug>, https://jobs.ashbyhq.com/<slug>,
https://apply.workable.com/<slug>, https://<slug>.recruitee.com, https://<slug>.teamtailor.com
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


def fetch_workable(slug):
    url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
    resp = requests.get(url, params={"details": "true"}, timeout=30)
    resp.raise_for_status()
    return [
        {
            "id": f"workable-{slug}-{job['shortcode']}",
            "title": job["title"],
            "company": slug,
            "location": ", ".join(filter(None, [job.get("city"), job.get("country")])),
            "url": job["url"],
            "description": strip_html(job.get("description", "")),
            "source": "workable",
            "posted_at": job.get("published_on"),
        }
        for job in resp.json().get("jobs", [])
    ]


def fetch_recruitee(slug):
    url = f"https://{slug}.recruitee.com/api/offers/"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return [
        {
            "id": f"recruitee-{slug}-{job['id']}",
            "title": job["title"],
            "company": job.get("company_name", slug),
            "location": "Remote" if job.get("remote") else "",
            "url": job["careers_url"],
            "description": strip_html(job.get("description", "")),
            "source": "recruitee",
            "posted_at": job.get("created_at"),
        }
        for job in resp.json().get("offers", [])
    ]


def fetch_teamtailor(slug):
    url = f"https://{slug}.teamtailor.com/jobs.json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    jobs = []
    for job in resp.json().get("items", []):
        posting = job.get("_jobposting", {})
        location = ""
        if posting.get("jobLocation"):
            addr = posting["jobLocation"][0].get("address", {})
            location = ", ".join(filter(None, [addr.get("addressLocality"), addr.get("addressCountry")]))
        jobs.append({
            "id": f"teamtailor-{slug}-{job['id']}",
            "title": job["title"],
            "company": posting.get("hiringOrganization", {}).get("name", slug),
            "location": location,
            "url": job["url"],
            "description": strip_html(job.get("content_html", "")),
            "source": "teamtailor",
            "posted_at": job.get("date_published"),
        })
    return jobs


def fetch(ats_config):
    jobs = []
    fetchers = [
        (ats_config.get("greenhouse", []), fetch_greenhouse),
        (ats_config.get("lever", []), fetch_lever),
        (ats_config.get("ashby", []), fetch_ashby),
        (ats_config.get("workable", []), fetch_workable),
        (ats_config.get("recruitee", []), fetch_recruitee),
        (ats_config.get("teamtailor", []), fetch_teamtailor),
    ]
    for slugs, fetcher in fetchers:
        for slug in slugs:
            try:
                jobs.extend(fetcher(slug))
            except requests.RequestException as e:
                print(f"Skipping {fetcher.__name__} slug '{slug}': {e}")
    return jobs
