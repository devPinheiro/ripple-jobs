"""Generate a tailored cover letter and resume highlight bullets for a scored job."""
import json

from anthropic import Anthropic

DRAFT_PROMPT = """You are helping a job applicant tailor their materials to one specific job posting.

Candidate profile (JSON):
{profile}

Job posting:
Title: {title}
Company: {company}
Description: {description}

Return ONLY valid JSON (no markdown fences) with this shape:
{{
  "cover_letter": string,   // 3-4 short paragraphs, specific to this role and company, no generic filler
  "resume_highlights": [string]  // 3-4 bullets pulled/adapted from the candidate's real experience, most relevant to this JD
}}
"""


def draft(job, profile, api_key):
    client = Anthropic(api_key=api_key)
    prompt = DRAFT_PROMPT.format(
        profile=json.dumps(profile),
        title=job["title"],
        company=job["company"],
        description=job.get("description", "")[:4000],
    )
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    return json.loads(text)
