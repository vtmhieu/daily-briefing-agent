"""
Deploys portal/index.html to the root of the gh-pages branch.
Run by: .github/workflows/deploy-portal.yml
"""

import os
import base64
import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_sha(path: str) -> str | None:
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=headers,
        params={"ref": "gh-pages"},
    )
    return r.json()["sha"] if r.status_code == 200 else None


def commit(path: str, content: bytes, message: str):
    payload = {
        "message": message,
        "content": base64.b64encode(content).decode(),
        "branch": "gh-pages",
    }
    sha = get_sha(path)
    if sha:
        payload["sha"] = sha

    r = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{path}",
        headers=headers,
        json=payload,
    )
    r.raise_for_status()


def main():
    with open("portal/index.html", "rb") as f:
        content = f.read()

    commit("index.html", content, "chore: deploy portal to gh-pages")
    print("Portal deployed to gh-pages/index.html")


if __name__ == "__main__":
    main()
