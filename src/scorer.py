"""Score a normalized job dict against the user's profile and preferences. Returns 0-100."""


def _text_of(job):
    return f"{job['title']} {job.get('description', '')}".lower()


def _stack_score(job_text, skills):
    matched = [s for s in skills if s.lower() in job_text]
    if not skills:
        return 0
    return min(len(matched), 6) / 6 * 40  # cap contribution at 40 pts


def _seniority_score(job_text, seniority):
    return 15 if seniority.lower() in job_text else 5


def _visa_score(job_text, prefs):
    if not prefs.get("visa_sponsorship_required"):
        return 20
    if any(p in job_text for p in prefs.get("visa_negative_phrases", [])):
        return 0
    if any(p in job_text for p in prefs.get("visa_positive_phrases", [])):
        return 25
    return 10  # unmentioned — plenty of sponsoring companies don't say so explicitly


REMOTE_ONLY_SOURCES = ("remotive", "weworkremotely", "remoteok", "jobicy", "himalayas")


def _remote_score(job, prefs):
    if not prefs.get("remote_only"):
        return 10
    location = job.get("location", "").lower()
    return 10 if "remote" in location or job["source"] in REMOTE_ONLY_SOURCES else 0


def _title_score(job_text, target_titles):
    return 10 if any(t.lower() in job_text for t in target_titles) else 0


def score_job(job, profile, prefs):
    job_text = _text_of(job)
    skills = profile.get("skills", [])
    breakdown = {
        "stack": round(_stack_score(job_text, skills), 1),
        "seniority": _seniority_score(job_text, prefs.get("seniority", "")),
        "visa": _visa_score(job_text, prefs),
        "remote": _remote_score(job, prefs),
        "title": _title_score(job_text, prefs.get("target_titles", [])),
    }
    total = round(sum(breakdown.values()))
    return total, breakdown
