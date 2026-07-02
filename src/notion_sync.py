"""Push scored + drafted jobs to Notion as database rows.

Uses Notion API version 2025-09-03 (notion-client's default), which introduced
multi-source databases: a database's columns live on its data source, not on the
database object itself, and pages are created under a data_source_id, not a
database_id. `create_database` sets the columns via `initial_data_source`;
`resolve_data_source_id` looks up the data source for a database_id so `push_job`
can target it.
"""
from notion_client import Client

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
            "JD Summary": {"rich_text": [{"text": {"content": job.get("description", "")[:2000]}}]},
            "Cover Letter": {"rich_text": [{"text": {"content": draft["cover_letter"][:2000]}}]},
            "Resume Highlights": {
                "rich_text": [{"text": {"content": "\n".join(draft["resume_highlights"])[:2000]}}]
            },
            "Date Added": {"date": {"start": date_added}},
        },
    )
