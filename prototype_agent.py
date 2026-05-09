"""
Prototype Agent
Reads a GitHub Issue title + body, asks Gemini to generate a plan and a
complete single-file HTML prototype, commits the HTML to the gh-pages branch,
and comments on the issue with the live GitHub Pages URL.

Triggered by: .github/workflows/prototype-on-issue.yml
"""

import os
import re
import base64
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]   # e.g. "vtmhieu/daily-briefing-agent"
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
ISSUE_BODY = os.environ.get("ISSUE_BODY", "").strip() or "(No description provided.)"

GH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

SYSTEM_PROMPT = """You are an expert frontend developer and product designer.
Given a business requirement, produce two things:

1. A concise 3-5 bullet plan/spec for what you will build.
2. A complete, beautiful, single-file HTML prototype.

HTML rules:
- Fully self-contained: inline CSS + JS only.
- You MAY use CDN links for Tailwind CSS, Alpine.js, Chart.js, or similar
  lightweight libraries — but nothing that requires a build step or a server.
- Look modern and professional. Use clean typography, spacing, and colour.
- Populate with realistic dummy data so the prototype feels alive.
- All interactions (filters, modals, tabs, charts) must work client-side.
- Must be responsive / mobile-friendly.

Return your response in EXACTLY this format — no text outside the tags:

<plan>
• bullet 1
• bullet 2
• bullet 3
</plan>
<prototype>
<!DOCTYPE html>
...full HTML...
</prototype>"""


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def ensure_gh_pages_branch():
    """Create the gh-pages branch if it doesn't already exist."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/branches/gh-pages"
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code == 200:
        return  # already exists

    # Get the SHA of the latest commit on main to branch from
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/ref/heads/main"
    r = requests.get(url, headers=GH_HEADERS)
    r.raise_for_status()
    sha = r.json()["object"]["sha"]

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/refs"
    r = requests.post(url, headers=GH_HEADERS, json={
        "ref": "refs/heads/gh-pages",
        "sha": sha,
    })
    r.raise_for_status()
    print("Created gh-pages branch.")


def get_file_sha(path: str) -> str | None:
    """Return the blob SHA of path on gh-pages (needed for updates)."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}"
    r = requests.get(url, headers=GH_HEADERS, params={"ref": "gh-pages"})
    if r.status_code == 200:
        return r.json()["sha"]
    return None


def commit_file(path: str, content: str, message: str):
    """Create or update a file on the gh-pages branch."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "gh-pages",
    }
    sha = get_file_sha(path)
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=GH_HEADERS, json=payload)
    r.raise_for_status()


def comment_on_issue(body: str):
    """Post a comment on the triggering issue."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{ISSUE_NUMBER}/comments"
    r = requests.post(url, headers=GH_HEADERS, json={"body": body})
    r.raise_for_status()


def pages_url() -> str:
    owner, repo = GITHUB_REPOSITORY.split("/")
    return f"https://{owner}.github.io/{repo}"


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def generate_prototype(title: str, body: str) -> tuple[str, str]:
    """
    Ask Gemini to produce a plan and a full HTML prototype.
    Returns (plan_markdown, html_string).
    """
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

    # 1. Make sure gh-pages branch exists
    ensure_gh_pages_branch()

    # 2. Generate plan + HTML
    plan, html = generate_prototype(ISSUE_TITLE, ISSUE_BODY)
    print("  Prototype generated.")

    # 3. Commit HTML to gh-pages
    file_path = f"prototypes/{ISSUE_NUMBER}/index.html"
    commit_file(
        path=file_path,
        content=html,
        message=f"feat: prototype for issue #{ISSUE_NUMBER} — {ISSUE_TITLE}",
    )
    print(f"  Committed {file_path} to gh-pages.")

    # 4. Build the live URL and comment
    live_url = f"{pages_url()}/prototypes/{ISSUE_NUMBER}/"
    source_url = f"https://github.com/{GITHUB_REPOSITORY}/blob/gh-pages/{file_path}"

    comment = f"""## ✅ Your prototype is ready

**[Open prototype →]({live_url})**

> If this is the first prototype in the repo, GitHub Pages may take 1–2 minutes to go live after being enabled.

### Plan
{plan}

---
*Generated by Gemini `{MODEL}` · [View HTML source]({source_url})*"""

    comment_on_issue(comment)
    print(f"  Commented on issue #{ISSUE_NUMBER}.")
    print(f"\nLive at: {live_url}")


if __name__ == "__main__":
    main()
