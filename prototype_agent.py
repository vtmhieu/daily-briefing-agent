"""
Prototype Agent
Reads a GitHub Issue (or a comment on one) and asks Gemini to generate or
update a complete single-file HTML prototype, commits it to gh-pages, and
comments back with the live URL.

Triggered by: .github/workflows/prototype-on-issue.yml
  - issues: types: [opened]      → new prototype
  - issue_comment: types: [created] → update existing prototype
"""

import os
import re
import json
import base64
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "").strip() or "(No description provided.)"
EVENT_TYPE = os.environ.get("EVENT_TYPE", "issues")   # "issues" or "issue_comment"
COMMENT_BODY = os.environ.get("COMMENT_BODY", "").strip()

IS_UPDATE = EVENT_TYPE == "issue_comment"

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

SYSTEM_PROMPT = """You are an elite frontend developer and product designer.
Given a business requirement, produce two things:

1. A concise 3-5 bullet plan/spec describing what you will build.
2. A complete, polished, single-file HTML prototype.

HTML rules:
- Fully self-contained: inline CSS + JS, no external files.
- You MAY load libraries via CDN: Tailwind CSS, Alpine.js, Chart.js, Lucide icons,
  or any other lightweight library that needs no build step.
- Design must be modern, clean, and professional — think Linear, Notion, or Vercel
  design quality. Use good typography, whitespace, and a consistent colour palette.
- Fill every component with realistic, domain-appropriate dummy data so the
  prototype feels like a real product, not a skeleton.
- All interactions — filters, modals, tabs, dropdowns, charts — must work
  fully client-side with no backend.
- Must be responsive and look great on both desktop and mobile.

Return your response in EXACTLY this format, with no text outside the tags:

<plan>
• bullet 1
• bullet 2
• bullet 3
</plan>
<prototype>
<!DOCTYPE html>
...complete HTML file...
</prototype>"""


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def ensure_gh_pages_branch():
    """Create the gh-pages branch if it doesn't already exist."""
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/branches/gh-pages",
        headers=GH_HEADERS,
    )
    if r.status_code == 200:
        return

    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/ref/heads/main",
        headers=GH_HEADERS,
    )
    r.raise_for_status()
    sha = r.json()["object"]["sha"]

    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/refs",
        headers=GH_HEADERS,
        json={"ref": "refs/heads/gh-pages", "sha": sha},
    )
    r.raise_for_status()
    print("  Created gh-pages branch.")


def get_file_sha(path: str) -> str | None:
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=GH_HEADERS,
        params={"ref": "gh-pages"},
    )
    return r.json()["sha"] if r.status_code == 200 else None


def get_file_content(path: str) -> str | None:
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=GH_HEADERS,
        params={"ref": "gh-pages"},
    )
    if r.status_code == 200:
        return base64.b64decode(r.json()["content"]).decode()
    return None


def commit_file(path: str, content: str, message: str):
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "gh-pages",
    }
    sha = get_file_sha(path)
    if sha:
        payload["sha"] = sha

    r = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=GH_HEADERS,
        json=payload,
    )
    r.raise_for_status()


def post_comment(body: str) -> int:
    """Post a comment on the issue and return the comment ID."""
    r = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}/comments",
        headers=GH_HEADERS,
        json={"body": body},
    )
    r.raise_for_status()
    return r.json()["id"]


def update_comment(comment_id: int, body: str):
    r = requests.patch(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/comments/{comment_id}",
        headers=GH_HEADERS,
        json={"body": body},
    )
    r.raise_for_status()


def pages_base_url() -> str:
    owner, repo = GITHUB_REPOSITORY.split("/")
    return f"https://{owner}.github.io/{repo}"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def update_registry(issue_number: str, issue_title: str):
    """Add or update this prototype in registry.json."""
    registry_path = "prototypes/registry.json"
    raw = get_file_content(registry_path)
    registry = json.loads(raw) if raw else {}
    registry[issue_number] = issue_title
    commit_file(
        registry_path,
        json.dumps(registry, indent=2, ensure_ascii=False),
        f"chore: update registry for #{issue_number}",
    )
    print("  Registry updated.")


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def generate_prototype(title: str, body: str, update_request: str = "") -> tuple[str, str]:
    """Call Gemini and return (plan, html)."""
    print(f"  Calling Gemini ({MODEL})...")

    if update_request:
        prompt = (
            f"Original requirement title: {title}\n\n"
            f"Original requirement details:\n{body}\n\n"
            f"The user wants to update the prototype with these changes:\n{update_request}\n\n"
            "Generate an updated plan and a fully updated prototype that incorporates the requested changes."
        )
    else:
        prompt = (
            f"Requirement title: {title}\n\n"
            f"Requirement details:\n{body}\n\n"
            "Generate the plan and prototype now."
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=8000,
        ),
    )

    text = response.text
    plan_match = re.search(r"<plan>(.*?)</plan>", text, re.DOTALL)
    proto_match = re.search(r"<prototype>(.*?)</prototype>", text, re.DOTALL)

    plan = plan_match.group(1).strip() if plan_match else "_Plan not generated._"
    html = proto_match.group(1).strip() if proto_match else (
        "<!DOCTYPE html><html><body><h1>Error: prototype not generated.</h1></body></html>"
    )

    return plan, html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    action = "Updating" if IS_UPDATE else "Generating"
    print(f"Prototype Agent — {action} prototype for issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    print("=" * 60)

    working_msg = (
        "⏳ **Updating your prototype...** hang tight, usually takes ~30 seconds."
        if IS_UPDATE else
        "⏳ **Generating your prototype...** hang tight, usually takes ~30 seconds."
    )
    working_comment_id = post_comment(working_msg)

    try:
        ensure_gh_pages_branch()

        plan, html = generate_prototype(
            ISSUE_TITLE,
            ISSUE_BODY,
            update_request=COMMENT_BODY if IS_UPDATE else "",
        )
        print("  Prototype generated.")

        file_path = f"prototypes/{ISSUE_NUMBER}/index.html"
        commit_msg = (
            f"fix: update prototype for issue #{ISSUE_NUMBER} — {ISSUE_TITLE}"
            if IS_UPDATE else
            f"feat: prototype for issue #{ISSUE_NUMBER} — {ISSUE_TITLE}"
        )
        commit_file(file_path, html, commit_msg)
        print(f"  Committed {file_path} to gh-pages.")

        # Only update the registry on first creation
        if not IS_UPDATE:
            update_registry(ISSUE_NUMBER, ISSUE_TITLE)

        base = pages_base_url()
        live_url = f"{base}/prototypes/{ISSUE_NUMBER}/"
        index_url = f"{base}/"
        source_url = f"https://github.com/{GITHUB_REPOSITORY}/blob/gh-pages/{file_path}"

        heading = "✅ Prototype updated" if IS_UPDATE else "✅ Your prototype is ready"
        note = "" if IS_UPDATE else "\n> If this is the first run, GitHub Pages may take 1–2 minutes to go live after being enabled in repo Settings.\n"

        update_comment(
            working_comment_id,
            f"""## {heading}

**[Open prototype →]({live_url})**
{note}
### Plan
{plan}

---
[All prototypes]({index_url}) · [View HTML source]({source_url}) · Generated by Gemini `{MODEL}`""",
        )

        print(f"\nDone. Live at: {live_url}")

    except Exception as e:
        update_comment(
            working_comment_id,
            f"## ❌ Generation failed\n\n```\n{e}\n```\n\nCheck the [Actions log](https://github.com/{GITHUB_REPOSITORY}/actions) for details.",
        )
        raise


if __name__ == "__main__":
    main()
