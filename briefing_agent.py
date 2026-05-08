"""
Daily Briefing Agent
Fetches and summarizes the day's top news across multiple domains using Claude,
then emails the briefing to you.
"""

import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic
from dotenv import load_dotenv

from email_sender import send_briefing_email
from domains import DOMAINS

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def fetch_domain_summary(domain_key: str, domain_config: dict) -> dict:
    """
    Ask Claude to research and summarize the top stories for one domain.
    Uses Claude's built-in web_search tool.
    """
    today = datetime.now().strftime("%A, %B %d, %Y")

    prompt = f"""Today is {today}. Find the top 5 most important news stories
in the domain of {domain_config['name']} from the last 24 hours.

Focus on: {domain_config['focus']}

For each story, provide:
- A 1-sentence headline
- A 1-sentence "why it matters" note
- The source name

Format the output as clean markdown bullet points. Be concise — total output
should fit in a 5-minute read. No preamble, just the bullets.
"""

    print(f"  Fetching {domain_config['name']}...")

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
            }],
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from final response (skipping tool-use blocks)
        text_parts = [
            block.text for block in response.content
            if hasattr(block, "text") and block.type == "text"
        ]
        summary = "\n".join(text_parts).strip()

        return {
            "key": domain_key,
            "name": domain_config["name"],
            "emoji": domain_config["emoji"],
            "summary": summary,
            "error": None,
        }
    except Exception as e:
        print(f"  Error fetching {domain_config['name']}: {e}")
        return {
            "key": domain_key,
            "name": domain_config["name"],
            "emoji": domain_config["emoji"],
            "summary": f"_Failed to fetch updates: {e}_",
            "error": str(e),
        }


def build_briefing() -> dict:
    """Run all domain agents in parallel and collect results."""
    print(f"Building briefing using model: {MODEL}\n")
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_domain_summary, key, cfg): key
            for key, cfg in DOMAINS.items()
        }
        for future in as_completed(futures):
            result = future.result()
            results[result["key"]] = result

    # Preserve original order of DOMAINS
    return {key: results[key] for key in DOMAINS.keys()}


def main():
    today = datetime.now().strftime("%A, %B %d, %Y")
    print(f"Daily Briefing Agent — {today}")
    print("=" * 50)

    briefing = build_briefing()

    print("\nSending email...")
    try:
        send_briefing_email(briefing, today)
        print("Briefing sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
