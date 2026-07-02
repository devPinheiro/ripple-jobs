import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from src import extract_profile, pipeline
from src.notion_sync import create_database


def cmd_extract_profile(args):
    if len(args) < 1:
        print("Usage: python main.py extract-profile <path-to-resume.pdf>")
        sys.exit(1)
    text = extract_profile.extract_text(args[0])
    profile = extract_profile.build_profile(text, os.environ["ANTHROPIC_API_KEY"])
    out_path = os.path.join(os.path.dirname(__file__), "data", "profile.json")
    with open(out_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Wrote {out_path}")


def cmd_setup_notion(args):
    token = os.environ.get("NOTION_TOKEN")
    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")
    if not token or not parent_page_id:
        print("Set NOTION_TOKEN and NOTION_PARENT_PAGE_ID in .env first (see README).")
        sys.exit(1)
    db_id = create_database(token, parent_page_id)
    print(f"Created Notion database: {db_id}")
    print("Add this to your .env as NOTION_DATABASE_ID")


def cmd_run(args):
    pipeline.run()


COMMANDS = {
    "extract-profile": cmd_extract_profile,
    "setup-notion": cmd_setup_notion,
    "run": cmd_run,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python main.py <{'|'.join(COMMANDS)}> [args]")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
