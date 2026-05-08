# 📰 Daily Briefing Agent

An AI agent that emails you a daily summary of the top news in **Tech & AI**, **Finance & Markets**, **Startups & VC**, and **Crypto** — fully automated via GitHub Actions.

Powered by Claude with web search.

## How it works

```
Cron (7am UTC daily)
        ↓
GitHub Actions runner
        ↓
For each domain in parallel:
  → Claude searches the web for top stories
  → Claude summarizes into bullet points
        ↓
HTML email assembled
        ↓
Sent via SMTP or SendGrid → your inbox
```

## Quick start

### 1. Clone and install

```bash
git clone <your-repo-url>
cd daily-briefing-agent
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Then edit .env and fill in your keys
```

You'll need:
- An **Anthropic API key** — get one at https://console.anthropic.com
- An **email provider**:
  - **SMTP option (free, easy)**: Gmail with an [App Password](https://support.google.com/accounts/answer/185833)
  - **SendGrid option (more reliable)**: A free SendGrid account (100 emails/day free tier)

### 3. Test it locally

```bash
python briefing_agent.py
```

You should receive a briefing email within ~60 seconds.

### 4. Deploy as a daily cron via GitHub Actions

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add these **secrets**:
   - `ANTHROPIC_API_KEY`
   - `EMAIL_FROM`, `EMAIL_TO`
   - For SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
   - For SendGrid: `SENDGRID_API_KEY`
4. (Optional) Add **variables**: `CLAUDE_MODEL`, `EMAIL_PROVIDER`
5. Go to the **Actions** tab and enable workflows
6. Trigger a test run with **"Run workflow"** on the *Daily Briefing* job

That's it — the briefing will arrive in your inbox every day at 7am UTC.

## Cost

Using **Claude Haiku 4.5** (the default), one daily run costs roughly **$0.05–0.15**. That's about **$2–5/month**. GitHub Actions is free for public repos and has a generous free tier for private ones.

## Customize

### Change domains

Edit `domains.py` — add, remove, or reword any domain. The agent will pick up the changes automatically.

### Change the schedule

Edit the `cron` line in `.github/workflows/daily-briefing.yml`. [Crontab.guru](https://crontab.guru) is helpful.

### Use a smarter model

Set `CLAUDE_MODEL=claude-sonnet-4-6` in your environment for richer summaries (~3× cost).

### Change format / depth

Edit the prompt in `briefing_agent.py` (the `prompt` variable inside `fetch_domain_summary`).

## Project structure

```
daily-briefing-agent/
├── briefing_agent.py        # Main orchestrator
├── domains.py               # Domain configuration
├── email_sender.py          # SMTP / SendGrid delivery + HTML rendering
├── requirements.txt
├── .env.example
├── .github/workflows/
│   └── daily-briefing.yml   # GitHub Actions cron job
└── README.md
```

## License

MIT
