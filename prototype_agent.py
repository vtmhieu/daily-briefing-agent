"""
Prototype Agent
Reads a GitHub Issue title + body, asks Gemini to generate a plan and a
complete single-file HTML prototype, commits the HTML to the gh-pages branch,
updates the prototype index page, and comments on the issue with the live URL.

Triggered by: .github/workflows/prototype-on-issue.yml
"""

import os
import re
import json
import base64
import html as htmllib
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "").strip() or "(No description provided.)"

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

    # Branch from main
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
    """Return the blob SHA of a file on gh-pages (needed to update it)."""
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=GH_HEADERS,
        params={"ref": "gh-pages"},
    )
    return r.json()["sha"] if r.status_code == 200 else None


def get_file_content(path: str) -> str | None:
    """Return the decoded content of a file on gh-pages."""
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=GH_HEADERS,
        params={"ref": "gh-pages"},
    )
    if r.status_code == 200:
        return base64.b64decode(r.json()["content"]).decode()
    return None


def commit_file(path: str, content: str, message: str):
    """Create or update a file on the gh-pages branch."""
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
    """Edit an existing comment."""
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
# Index page
# ---------------------------------------------------------------------------

def build_index_html(prototypes: dict) -> str:
    """Generate the index.html listing all prototypes, newest first."""
    sorted_items = sorted(
        prototypes.items(),
        key=lambda x: int(x[0]) if x[0].isdigit() else 0,
        reverse=True,
    )
    base = pages_base_url()

    cards = ""
    for num, title in sorted_items:
        safe_title = htmllib.escape(title)
        cards += f"""
    <a href="{base}/prototypes/{num}/" class="card" target="_blank">
      <span class="num">#{num}</span>
      <span class="title">{safe_title}</span>
      <span class="arrow">→</span>
    </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prototypes</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f9f9f9;
      color: #111;
      min-height: 100vh;
      padding: 60px 24px;
    }}
    .wrap {{ max-width: 600px; margin: 0 auto; }}
    header {{ margin-bottom: 40px; }}
    header h1 {{ font-size: 22px; font-weight: 600; margin-bottom: 6px; }}
    header p {{ font-size: 14px; color: #888; }}
    header a {{ color: #888; }}
    .card {{
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 16px 0;
      border-bottom: 1px solid #eee;
      text-decoration: none;
      color: inherit;
      transition: color .15s;
    }}
    .card:first-child {{ border-top: 1px solid #eee; }}
    .card:hover {{ color: #0066ff; }}
    .num {{ font-size: 12px; color: #bbb; min-width: 36px; }}
    .title {{ font-size: 15px; flex: 1; }}
    .arrow {{ font-size: 16px; color: #ccc; }}
    .card:hover .arrow {{ color: #0066ff; }}
    .empty {{ color: #aaa; font-size: 14px; padding-top: 24px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Prototypes</h1>
      <p>Generated by the Prototype Agent ·
        <a href="https://github.com/{GITHUB_REPOSITORY}" target="_blank">View repo</a>
      </p>
    </header>
    {"".join(cards) if cards else '<p class="empty">No prototypes yet.</p>'}
  </div>
</body>
</html>"""


def update_index(issue_number: str, issue_title: str):
    """Load the prototype registry, add the new entry, and rebuild index.html."""
    registry_path = "prototypes/registry.json"

    raw = get_file_content(registry_path)
    registry = json.loads(raw) if raw else {}

    registry[issue_number] = issue_title

    commit_file(
        registry_path,
        json.dumps(registry, indent=2, ensure_ascii=False),
        f"chore: update registry for #{issue_number}",
    )
    commit_file(
        "index.html",
        build_index_html(registry),
        f"chore: rebuild index for #{issue_number}",
    )
    print("  Index updated.")


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def generate_prototype(title: str, body: str) -> tuple[str, str]:
    """Call Gemini and return (plan, html)."""
    print(f"  Calling Gemini ({MODEL})...")

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
    print(f"Prototype Agent — issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    print("=" * 60)

    # Post an instant "working" comment so the user knows the agent is running
    working_comment_id = post_comment(
        "⏳ **Generating your prototype...** hang tight, usually takes ~30 seconds."
    )

    try:
        # Ensure gh-pages branch exists
        ensure_gh_pages_branch()

        # Generate plan + HTML via Gemini
        plan, html = generate_prototype(ISSUE_TITLE, ISSUE_BODY)
        print("  Prototype generated.")

        # Commit the prototype HTML
        file_path = f"prototypes/{ISSUE_NUMBER}/index.html"
        commit_file(
            file_path,
            html,
            f"feat: prototype for issue #{ISSUE_NUMBER} — {ISSUE_TITLE}",
        )
        print(f"  Committed {file_path} to gh-pages.")

        # Rebuild the index page
        update_index(ISSUE_NUMBER, ISSUE_TITLE)

        # Build URLs
        base = pages_base_url()
        live_url = f"{base}/prototypes/{ISSUE_NUMBER}/"
        index_url = f"{base}/"
        source_url = (
            f"https://github.com/{GITHUB_REPOSITORY}/blob/gh-pages/{file_path}"
        )

        # Replace the working comment with the final result
        update_comment(
            working_comment_id,
            f"""## ✅ Your prototype is ready

**[Open prototype →]({live_url})**

> If this is the first run, GitHub Pages may take 1–2 minutes to go live after being enabled in repo Settings.

### Plan
{plan}

---
[All prototypes]({index_url}) · [View HTML source]({source_url}) · Generated by Gemini `{MODEL}`""",
        )

        print(f"\nDone. Live at: {live_url}")

    except Exception as e:
        # Update the comment to show the error instead of leaving it hanging
        update_comment(
            working_comment_id,
            f"## ❌ Generation failed\n\n```\n{e}\n```\n\nCheck the [Actions log](https://github.com/{GITHUB_REPOSITORY}/actions) for details.",
        )
        raise


if __name__ == "__main__":
    main()
