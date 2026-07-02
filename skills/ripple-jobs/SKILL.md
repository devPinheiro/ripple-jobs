---
name: ripple-jobs
description: Use when running, setting up, or troubleshooting the ripple-jobs pipeline — fetching frontend job listings, building a resume-based profile, scoring and drafting applications, or syncing results to a Notion job queue.
---

# ripple-jobs

## Overview

Operates the ripple-jobs CLI (`main.py`): fetches frontend job listings from ToS-safe sources,
scores them against a resume-derived profile, drafts a cover letter + resume highlights per match,
and queues results in Notion for manual review. It never submits applications — approval and
applying stay entirely manual.

## When to Use

- User asks to run their job search, check for new job matches, or refresh their job queue
- User is setting up the tool for the first time (profile extraction, Notion integration)
- A `main.py` command fails and needs troubleshooting
- User wants to tune scoring, add a company's ATS board, or adjust visa/remote preferences

**Do not use this skill to attempt automated job applications, LinkedIn/Wellfound scraping, or
browser automation against job boards** — that's an explicit non-goal of this tool (ToS/ban risk).
If asked to go further than drafting, say so instead of improvising a workaround.

## Locating the repo

Find the ripple-jobs checkout (contains `main.py`, `src/pipeline.py`, `config/preferences.yaml`).
Check common project directories, or ask the user for the path if it isn't obvious. All commands
below run from the repo root with the venv active:

```
source .venv/bin/activate   # first time: python3 -m venv .venv && pip install -r requirements.txt
```

## Commands

| Task | Command | Requires in `.env` |
|---|---|---|
| Build/update profile from resume | `python main.py extract-profile /path/to/resume.pdf` | `ANTHROPIC_API_KEY` |
| One-time Notion database setup | `python main.py setup-notion` | `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID` |
| Run the full pipeline | `python main.py run` | `ANTHROPIC_API_KEY`, `NOTION_TOKEN`, `NOTION_DATABASE_ID` |

`.env` doesn't exist by default — copy `.env.example` to `.env` if missing. Never commit it.

`run` is safe to re-run anytime (daily, on request, whatever) — it dedupes against `data/seen.json`,
so already-processed jobs are skipped rather than re-drafted or re-queued. Before running it for a
user, do a quick pre-flight: confirm `.env` has the three keys above set, and that `data/profile.json`
exists and has a non-empty `skills` list (not left over as `profile.example.json` placeholder data).
Catching those two upfront is faster than diagnosing a bad run after the fact.

## Troubleshooting

- **`Could not find page with ID: ...`** (from `setup-notion`) — the Notion integration isn't
  connected to that page. In Notion: open the page → "···" → Connections → add the integration.
  A correct page ID doesn't matter if the page isn't shared with the integration.
- **Database created but only has a "Name" column** — `notion-client` is older than 3.0.0 and
  doesn't default to Notion's multi-source-database API; run `pip install -U notion-client` inside
  the venv, archive the broken database in Notion, and re-run `setup-notion`.
- **Scores all cluster low** — `data/profile.json` is likely missing, empty, or was accidentally
  left as `profile.example.json`'s placeholder content. Re-run `extract-profile`.
- **A source returns nothing** — `pipeline.fetch_all()` catches and logs per-source errors rather
  than failing the whole run; check console output for that source's specific error (rate limit,
  API shape change) instead of assuming the whole pipeline is broken.
- **Notion fields look truncated** — rich_text fields are capped at 2000 characters by design
  (Notion's block limit). Expected, not a bug.
- **Missing dependency errors** — run `pip install -r requirements.txt` inside the activated venv.

## Key files

- `config/preferences.yaml` — visa/remote/seniority/title preferences, ATS company boards to watch,
  `min_score_to_queue`
- `data/profile.json` — the user's real profile (gitignored; never overwrite with
  `profile.example.json`'s placeholder content)
- `data/seen.json` — dedup cache; deleting it makes the next run re-process every job as new
