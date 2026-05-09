# AI Agent Suite

Two free, fully automated AI agents that run on GitHub Actions — no servers, no monthly fees.

Powered by **Gemini 2.0 Flash** (free tier) + **GitHub Pages**.

---

## Agent 1: Daily Briefing

Emails you a daily summary of the top news across **Tech & AI**, **Finance & Markets**, **Startups & VC**, and **Crypto** — every morning at 7am UTC.

```
Cron (7am UTC daily)
        ↓
GitHub Actions
        ↓
For each domain in parallel:
  → Gemini searches the web for top stories
  → Summarizes into bullet points
        ↓
HTML email assembled
        ↓
Sent via SMTP or SendGrid → your inbox
```

---

## Agent 2: Prompt-to-Prototype

Open a GitHub Issue describing a UI requirement. The agent generates a working HTML prototype and deploys it to GitHub Pages — all automatically.

```
You open a GitHub Issue
  "Build me a CRM dashboard for tracking leads"
        ↓
GitHub Actions fires
        ↓
Gemini generates:
  → A 3-5 bullet plan/spec
  → A complete single-file HTML prototype
        ↓
HTML committed to gh-pages branch
        ↓
Bot comments on your issue with the live URL
        ↓
https://your-username.github.io/repo/prototypes/1/
```

---

## Cost

Everything here is **free**:

| Component | Free tier |
|---|---|
| Gemini 2.0 Flash | Free via Google AI Studio |
| GitHub Actions | Free for public repos |
| GitHub Pages | Free |
| SMTP via Gmail | Free with App Password |

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd daily-briefing-agent
pip install -r requirements.txt
```

### 2. Get a Gemini API key

1. Go to **aistudio.google.com**
2. Sign in with Google → **Get API key**
3. Copy it — starts with `AIza...`

No credit card required.

### 3. Set up environment (for local runs)

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY + email settings
```

### 4. Add GitHub secrets

Go to your repo → **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | From Google AI Studio |
| `EMAIL_FROM` | Sender email address |
| `EMAIL_TO` | Your email address |
| `SMTP_HOST` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | e.g. `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail [App Password](https://support.google.com/accounts/answer/185833) |

Using SendGrid instead of SMTP? Add `SENDGRID_API_KEY` and set the variable `EMAIL_PROVIDER=sendgrid`.

### 5. Enable GitHub Pages (for the prototype agent)

Go to your repo → **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: **`gh-pages`** / `/ (root)`
- Save

### 6. Enable Actions

Go to the **Actions** tab and enable workflows if prompted.

---

## Running

### Daily Briefing — locally

```bash
python briefing_agent.py
```

You'll receive a briefing email within ~30 seconds.

### Daily Briefing — automated

Runs automatically every day at **7am UTC**. To trigger manually:
- Actions tab → **Daily Briefing** → **Run workflow**

### Prototype Agent — open an Issue

Write your requirement as a GitHub Issue (title + body). The workflow fires automatically on submission. Example:

> **Title:** Sales pipeline dashboard
>
> **Body:** I need a Kanban-style board showing deals by stage (Lead, Proposal, Negotiation, Closed). Each card should show company name, deal value, and owner. Include a summary bar at the top with totals per stage.

The bot will comment back on your issue with a live link in ~30 seconds.

---

## Customize

### Change news domains

Edit `domains.py` — add, remove, or reword any domain. The briefing agent picks up changes automatically.

### Change the briefing schedule

Edit the `cron` line in `.github/workflows/daily-briefing.yml`. [Crontab.guru](https://crontab.guru) is helpful.

### Use a smarter model

Set `GEMINI_MODEL=gemini-1.5-pro` or `gemini-2.5-pro` as a GitHub Actions variable for richer output.

### Change the briefing format

Edit the prompt in `briefing_agent.py` inside `fetch_domain_summary`.

### Change the prototype style

Edit `SYSTEM_PROMPT` in `prototype_agent.py` to change the design style, output format, or libraries used.

---

## Project structure

```
daily-briefing-agent/
├── briefing_agent.py             # Daily briefing orchestrator
├── prototype_agent.py            # Prompt-to-prototype generator
├── domains.py                    # News domain configuration
├── email_sender.py               # SMTP / SendGrid delivery + HTML rendering
├── requirements.txt
├── .env.example
├── .github/workflows/
│   ├── daily-briefing.yml        # Cron: runs briefing_agent.py daily
│   └── prototype-on-issue.yml    # Trigger: runs prototype_agent.py on new issues
└── README.md
```

---

## License

MIT
