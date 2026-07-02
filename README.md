# ripple-jobs

A personal, human-in-the-loop pipeline for frontend job hunting: it fetches listings from ToS-safe
sources, scores them against your profile, drafts a tailored cover letter and resume highlights for
each strong match, and queues everything as a card in a Notion database for you to review. **Nothing
is ever submitted automatically** — you read each draft, edit if you want, and apply yourself.

Built out of a real job search, not as a demo. The design choice that matters most: it optimizes for
fewer, better-targeted applications rather than spray-and-pray volume.

## Why this exists

Most "auto-apply" tools either violate job board terms of service (automated LinkedIn scraping/
submission risks account bans) or produce generic, low-quality applications that perform worse than
no automation at all. This tool draws the line differently:

- **Sourcing** only from boards/APIs that are public and meant to be consumed programmatically.
- **Scoring** to surface the roles actually worth your time, instead of showing you everything.
- **Drafting** to save the blank-page cost of tailoring materials, not to replace your judgment.
- **Applying** stays manual, always.

## Architecture

```
 ┌─────────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
 │   Sources   │ ──▶ │  Dedupe  │ ──▶ │  Scorer  │ ──▶ │  Drafter   │ ──▶ │ Notion │
 │ (fetch jobs)│     │(seen.json│     │ (profile │     │ (Anthropic │     │(queue) │
 │             │     │  cache)  │     │  match)  │     │  API)      │     │        │
 └─────────────┘     └──────────┘     └──────────┘     └────────────┘     └────────┘
```

Each stage is a plain Python module — no framework, no job queue, no database beyond a flat
`data/seen.json` dedup cache. `main.py run` runs the whole pipeline once; you re-run it (cron,
`launchd`, or by hand) whenever you want fresh listings.

### Directory layout

```
config/
  preferences.yaml     # things a resume can't tell us: visa needs, target titles, ATS boards to watch
data/
  profile.json          # your structured profile (gitignored — contains PII)
  profile.example.json  # the schema, with placeholder data, so you can see the shape
  seen.json              # job IDs already processed, so re-runs don't re-queue them (gitignored)
src/
  extract_profile.py     # resume PDF -> structured profile.json, via Claude
  scorer.py               # profile+prefs -> 0-100 match score per job
  drafter.py               # job+profile -> cover letter + resume highlights, via Claude
  notion_sync.py            # creates the Notion DB, pushes job cards
  pipeline.py                # orchestrates fetch -> dedupe -> score -> draft -> push
  text_utils.py                # shared HTML-stripping for messy source descriptions
  sources/
    remotive.py                # public API
    wwr.py                      # WeWorkRemotely public RSS
    remoteok.py                  # public API
    ats_boards.py                 # Greenhouse/Lever/Ashby by company slug
main.py                            # CLI: extract-profile | setup-notion | run
```

## Job sources — and why LinkedIn/Wellfound aren't in the list

| Source | How | Notes |
|---|---|---|
| Remotive | Public JSON API | The API's `search` param doesn't actually filter server-side (verified by testing) — we pull the whole `software-dev` category and let the scorer do the filtering. |
| WeWorkRemotely | Public RSS feed | Descriptions arrive as raw HTML; stripped via `text_utils.strip_html`. |
| RemoteOK | Public JSON API | Filtered client-side to tags like `frontend`/`react`/`typescript`/`vue`/`javascript`. |
| Greenhouse / Lever / Ashby | Public per-company job-board JSON APIs | Opt-in per company slug in `config/preferences.yaml`. These endpoints exist specifically so companies can embed their listings elsewhere — using them isn't scraping in any meaningful sense. |
| ~~LinkedIn~~ | — | Automated interaction with LinkedIn (scraping search results or auto-applying) violates their ToS and risks account restriction/ban. Not implemented, and not planned. |
| ~~Wellfound~~ | — | Wellfound (formerly AngelList Talent) deprecated its public jobs API years ago. The only way to pull listings now is scraping the logged-in search UI — same risk profile as LinkedIn. Not implemented. |

If you want LinkedIn/Wellfound listings, the intended workflow is manual: copy a posting URL into
Notion yourself and treat it like any other row. This tool intentionally does not automate that.

## Setup

### 1. Install

```bash
git clone https://github.com/devPinheiro/ripple-jobs.git
cd ripple-jobs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Anthropic API key

Get one from https://console.anthropic.com and put it in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

This powers both profile extraction (one-time, per resume) and per-job drafting (each run).

### 3. Build your profile

```bash
python main.py extract-profile /path/to/your/resume.pdf
```

This parses the PDF, sends the text to Claude with a fixed JSON schema (see
`src/extract_profile.py:PROFILE_SCHEMA_PROMPT`), and writes `data/profile.json`. Re-run this
whenever your resume changes — it's a cheap, single API call.

Visa sponsorship needs, target seniority, and title preferences aren't reliably present in a resume,
so they live separately in `config/preferences.yaml` (see step 5).

### 4. Notion integration

Notion access is two credentials plus a one-time database creation:

1. **Create the integration**: https://www.notion.so/my-integrations → "New integration" → name it,
   pick your workspace → copy the **Internal Integration Secret** → `NOTION_TOKEN` in `.env`.
2. **Give it a page to work in**: create (or pick) a Notion page that will hold the job board. Open
   it → "···" menu (top right) → **Connections** → connect your integration. Skipping this step is
   the #1 cause of a `Could not find page with ID` error later — the API can only see pages
   explicitly shared with the integration, regardless of whether you (the human) can see them.
3. **Get the page ID**: from the page URL, e.g. `notion.so/My-Job-Search-1a2b3c4d5e6f7890abcd1234ef567890`
   → the 32-character trailing string is the ID. Put it in `.env` as `NOTION_PARENT_PAGE_ID` (with or
   without dashes both work — the API normalizes it).
4. **Create the database**:
   ```bash
   python main.py setup-notion
   ```
   This prints a database ID — add it to `.env` as `NOTION_DATABASE_ID`. It creates one database
   named "Job Applications" with these columns: Role, Company, Score, Status (select: Queued →
   Approved → Applied → Response → Closed), Source, Apply Link, JD Summary, Cover Letter, Resume
   Highlights, Date Added.

### 5. Preferences

Edit `config/preferences.yaml`:

```yaml
target_titles: ["Frontend Engineer", "Senior Frontend Engineer", ...]
seniority: "Senior"
visa_sponsorship_required: true
visa_positive_phrases: ["visa sponsorship", "will sponsor", ...]
visa_negative_phrases: ["no sponsorship", "must be authorized to work", ...]
remote_only: true
ats_boards:
  greenhouse: ["airbnb"]   # add company slugs from their public job board URLs
  lever: []
  ashby: []
min_score_to_queue: 60
```

Company slugs are the identifier in the company's public board URL:
`boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, `jobs.ashbyhq.com/<slug>`.

## Usage

### Running the pipeline

```bash
python main.py run
```

Each run:
1. Fetches every configured source.
2. Drops anything already in `data/seen.json` (so re-runs don't re-process old listings).
3. Scores everything new against `data/profile.json` + `config/preferences.yaml`.
4. For anything scoring ≥ `min_score_to_queue`, drafts a cover letter and resume highlights, then
   creates a Notion row with status **Queued**.
5. Writes the updated seen-set back to disk.

Run it daily via cron or `launchd` to keep the board fresh without re-reviewing old listings:

```cron
0 8 * * * cd /path/to/ripple-jobs && .venv/bin/python main.py run >> run.log 2>&1
```

### The review workflow

Everything lands in Notion as **Queued**. The intended flow per card:

1. Read the JD Summary and the drafted cover letter.
2. Edit the cover letter if it needs a human touch (it usually will, at least a little).
3. Move Status to **Approved** once you're happy with it.
4. Apply through the Apply Link, using the drafted cover letter and resume highlights.
5. Move Status to **Applied**, then **Response** or **Closed** as things develop.

Nothing after step 4 is automated — this tool's job ends at "give you a good enough draft that
applying is a five-minute task instead of a thirty-minute one."

### Scoring, in detail

`src/scorer.py` computes a 0-100 score as a weighted sum:

| Component | Max points | How it's computed |
|---|---|---|
| Stack match | 40 | Counts how many of your `profile.json` skills appear in the job text, capped at 6 matches |
| Seniority | 15 | 15 if `preferences.seniority` appears in the job text, else 5 |
| Visa signal | 25 | 25 if a positive phrase is found, 0 if a negative phrase is found, 10 if neither (most sponsoring companies don't say so explicitly) |
| Remote-friendly | 10 | 10 if "remote" appears in location or the source is a remote-only aggregator |
| Title match | 10 | 10 if any `target_titles` entry appears in the job text |

If you're seeing too much noise, tighten `min_score_to_queue` in `config/preferences.yaml` first —
it's the cheapest lever. If specific components are miscalibrated for your situation, edit the
weights directly in `scorer.py`; they're small, readable functions by design.

### Extending sources

Every source module returns a list of dicts with the same shape:

```python
{
    "id": "unique-per-source-string",
    "title": str,
    "company": str,
    "location": str,
    "url": str,
    "description": str,   # plain text — strip HTML with src.text_utils.strip_html if needed
    "source": str,
    "posted_at": str | None,
}
```

To add a new source: write a `fetch()` function returning that shape in a new file under
`src/sources/`, then wire it into `pipeline.fetch_all()`. If the source's API paginates or the
response includes HTML/entity-encoded text, check `text_utils.strip_html` before reinventing it —
it already handles the double-encoding some ATS platforms use (see `ats_boards.py`'s Greenhouse
`content=true` fetch for an example).

### Extending the draft prompt

`src/drafter.py:DRAFT_PROMPT` is a single template string. Edit it directly to change tone, length,
or structure of the generated cover letter/highlights — there's no abstraction layer to fight.

## Claude Code skill

If you use [Claude Code](https://claude.com/claude-code), `skills/ripple-jobs/SKILL.md` packages
the setup steps, commands, and troubleshooting from this README into an installable skill, so you
can just say "run my job search" or "check my Notion job queue" instead of pasting commands.

Install it:

```bash
# Recommended
npx skills add devPinheiro/ripple-jobs -g -a claude-code

# Manual
mkdir -p ~/.claude/skills/ripple-jobs
cp skills/ripple-jobs/SKILL.md ~/.claude/skills/ripple-jobs/SKILL.md
```

The skill is scoped to the tool's boundaries — it explicitly refuses to improvise auto-apply or
LinkedIn/Wellfound automation even if asked, since that's a deliberate non-goal of this project.

## Troubleshooting

**`Could not find page with ID: ...` from `setup-notion`** — the integration hasn't been connected
to that page. Open the page in Notion → "···" → Connections → add your integration, then retry.

**Notion rows look empty in some columns** — `push_job` truncates long text fields at 2000
characters (Notion's rich_text limit per block). The full description/cover letter length is capped
before drafting (`drafter.py` truncates job descriptions at 4000 chars going into the prompt).

**A job source returns nothing / errors** — `pipeline.fetch_all()` catches per-source exceptions and
logs a "Skipping source" message rather than failing the whole run. Check the printed message for
the underlying error (rate limit, API shape change, etc.).

**Scores all cluster low** — check that `data/profile.json` actually has a populated `skills` list;
if `extract_profile.py` mis-parsed your resume, `_stack_score` in `scorer.py` will have nothing to
match against.

## Roadmap / ideas not yet built

- A lightweight web UI instead of Notion, for people who don't want a Notion dependency
- Salary range parsing/filtering
- De-duplicating the same job posted across multiple sources
- Slack/email digest instead of (or alongside) Notion

## Contributing

Issues and PRs welcome. This started as a personal tool, so expect some rough edges outside the
happy path — if you hit one, a PR with a fix is more useful than a bug report, but either is fine.

## License

MIT — see [LICENSE](LICENSE).
