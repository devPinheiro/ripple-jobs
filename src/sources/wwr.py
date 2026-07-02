"""WeWorkRemotely public RSS feed for the programming category."""
import hashlib

import feedparser

from src.text_utils import strip_html

FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


def fetch():
    feed = feedparser.parse(FEED_URL)
    jobs = []
    for entry in feed.entries:
        title = entry.title
        company = title.split(":")[0].strip() if ":" in title else ""
        role = title.split(":", 1)[1].strip() if ":" in title else title
        job_id = "wwr-" + hashlib.sha1(entry.link.encode()).hexdigest()[:12]
        jobs.append({
            "id": job_id,
            "title": role,
            "company": company,
            "location": "Remote",
            "url": entry.link,
            "description": strip_html(entry.get("summary", "")),
            "source": "weworkremotely",
            "posted_at": entry.get("published"),
        })
    return jobs
