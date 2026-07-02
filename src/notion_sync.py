"""Push scored + drafted jobs to Notion as database rows."""
from notion_client import Client


def create_database(token, parent_page_id):
    client = Client(auth=token)
    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Job Applications"}}],
        properties={
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
        },
    )
    return db["id"]


def push_job(token, database_id, job, score, draft, date_added):
    client = Client(auth=token)
    client.pages.create(
        parent={"database_id": database_id},
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
