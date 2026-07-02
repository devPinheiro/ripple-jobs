"""Parse a resume PDF into a structured profile dict used by the scorer and drafter."""
import json

import pdfplumber
from anthropic import Anthropic

PROFILE_SCHEMA_PROMPT = """You are extracting a structured profile from a resume for a job-matching system.

Return ONLY valid JSON (no markdown fences) matching this shape:
{
  "name": string,
  "title": string,
  "years_experience": number,
  "email": string,
  "links": {"linkedin": string|null, "github": string|null, "website": string|null},
  "skills": [string],
  "experience": [
    {
      "company": string,
      "title": string,
      "start": string,
      "end": string,
      "highlights": [string]
    }
  ],
  "education": [string]
}

Resume text:
---
{resume_text}
---
"""


def extract_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def build_profile(resume_text, api_key):
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": PROFILE_SCHEMA_PROMPT.replace("{resume_text}", resume_text),
        }],
    )
    text = message.content[0].text.strip()
    return json.loads(text)
