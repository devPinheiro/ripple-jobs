"""Fetch -> dedupe -> score -> draft -> push to Notion."""
import json
import os
from datetime import date

import yaml

from src import scorer, drafter, notion_sync
from src.sources import remotive, wwr, remoteok, ats_boards

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
PROFILE_PATH = os.path.join(BASE_DIR, "data", "profile.json")
PREFS_PATH = os.path.join(BASE_DIR, "config", "preferences.yaml")
SEEN_PATH = os.path.join(BASE_DIR, "data", "seen.json")


def load_profile():
    with open(PROFILE_PATH) as f:
        return json.load(f)


def load_prefs():
    with open(PREFS_PATH) as f:
        return yaml.safe_load(f)


def load_seen():
    if not os.path.exists(SEEN_PATH):
        return set()
    with open(SEEN_PATH) as f:
        return set(json.load(f))


def save_seen(seen_ids):
    with open(SEEN_PATH, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def fetch_all(prefs):
    jobs = []
    for fetcher, label in [(remotive.fetch, "remotive"), (wwr.fetch, "weworkremotely"), (remoteok.fetch, "remoteok")]:
        try:
            jobs.extend(fetcher())
        except Exception as e:
            print(f"Skipping source {label}: {e}")
    jobs.extend(ats_boards.fetch(prefs.get("ats_boards", {})))
    return jobs


def run():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    notion_token = os.environ.get("NOTION_TOKEN")
    notion_db = os.environ.get("NOTION_DATABASE_ID")
    if not all([api_key, notion_token, notion_db]):
        raise SystemExit("Missing ANTHROPIC_API_KEY, NOTION_TOKEN, or NOTION_DATABASE_ID in environment/.env")

    profile = load_profile()
    prefs = load_prefs()
    seen = load_seen()
    data_source_id = notion_sync.resolve_data_source_id(notion_token, notion_db)

    jobs = fetch_all(prefs)
    print(f"Fetched {len(jobs)} jobs across all sources")

    new_jobs = [j for j in jobs if j["id"] not in seen]
    print(f"{len(new_jobs)} new (not previously seen)")

    min_score = prefs.get("min_score_to_queue", 60)
    queued = 0
    for job in new_jobs:
        score, breakdown = scorer.score_job(job, profile, prefs)
        seen.add(job["id"])
        if score < min_score:
            continue
        try:
            job_draft = drafter.draft(job, profile, api_key)
            notion_sync.push_job(notion_token, data_source_id, job, score, job_draft, date.today().isoformat())
            queued += 1
            print(f"Queued [{score}] {job['title']} @ {job['company']} ({job['source']})")
        except Exception as e:
            print(f"Failed to draft/push {job['title']} @ {job['company']}: {e}")

    save_seen(seen)
    print(f"Done. {queued} jobs queued to Notion.")
