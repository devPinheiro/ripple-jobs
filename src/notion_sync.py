"""Push scored + drafted jobs to Notion as database rows.

Uses Notion API version 2025-09-03 (notion-client's default), which introduced
multi-source databases: a database's columns live on its data source, not on the
database object itself, and pages are created under a data_source_id, not a
database_id. `create_database` sets the columns via `initial_data_source`;
`resolve_data_source_id` looks up the data source for a database_id so `push_job`
can target it.
"""
from notion_client import Client

# Notion's rich_text limit is 2000 chars counted as UTF-16 code units, but Python
# len()/slicing counts Unicode code points — a single astral character (e.g. some
# emoji) counts as 1 code point but 2 UTF-16 units, so a naive [:2000] slice can
# still land over the limit. Truncate with margin instead of matching exactly.
TEXT_LIMIT = 1900

DATABASE_PROPERTIES = {
    "Role": {"title": {}},
    "Company": {"rich_text": {}},
    "Score": {"number": {}},
    "Status": {
        "select": {
            "options": [
                {"name": "Queued", "color": "gray"},
                {"name": "Approved", "color": "blue"},
                {"name": "Applied", "color": "green"},
                {"name": "Response", "color": "yellow"},
                {"name": "Closed", "color": "red"},
            ]
        }
    },
    "Source": {"rich_text": {}},
    "Apply Link": {"url": {}},
    "JD Summary": {"rich_text": {}},
    "Cover Letter": {"rich_text": {}},
    "Resume Highlights": {"rich_text": {}},
    "Date Added": {"date": {}},
}


def create_database(token, parent_page_id):
    client = Client(auth=token)
    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Job Applications"}}],
        initial_data_source={"properties": DATABASE_PROPERTIES},
    )
    return db["id"]


def resolve_data_source_id(token, database_id):
    client = Client(auth=token)
    db = client.databases.retrieve(database_id)
    return db["data_sources"][0]["id"]


def push_job(token, data_source_id, job, score, draft, date_added):
    client = Client(auth=token)
    client.pages.create(
        parent={"type": "data_source_id", "data_source_id": data_source_id},
        properties={
            "Role": {"title": [{"text": {"content": job["title"]}}]},
            "Company": {"rich_text": [{"text": {"content": job["company"]}}]},
            "Score": {"number": score},
            "Status": {"select": {"name": "Queued"}},
            "Source": {"rich_text": [{"text": {"content": job["source"]}}]},
            "Apply Link": {"url": job["url"]},
            "JD Summary": {"rich_text": [{"text": {"content": job.get("description", "")[:TEXT_LIMIT]}}]},
            "Cover Letter": {"rich_text": [{"text": {"content": draft["cover_letter"][:TEXT_LIMIT]}}]},
            "Resume Highlights": {
                "rich_text": [{"text": {"content": "\n".join(draft["resume_highlights"])[:TEXT_LIMIT]}}]
            },
            "Date Added": {"date": {"start": date_added}},
        },
    )
