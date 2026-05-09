"""
Daily Briefing Agent
Fetches and summarizes the day's top news across multiple domains using Gemini,
then emails the briefing to you.
"""

import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from dotenv import load_dotenv

from email_sender import send_briefing_email
from domains import DOMAINS

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def fetch_domain_summary(domain_key: str, domain_config: dict) -> dict:
    """
    Ask Gemini to research and summarize the top stories for one domain.
    Uses Gemini's built-in Google Search grounding tool.
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
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                max_output_tokens=1500,
            ),
        )

        summary = response.text.strip()

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
