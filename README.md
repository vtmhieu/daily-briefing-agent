# Prototype Agent

Turn a GitHub Issue into a live, clickable UI prototype in ~30 seconds — fully automated, completely free.

Write your requirement as a GitHub Issue. The agent reads it, generates a working HTML prototype with Gemini, deploys it to GitHub Pages, and comments back with a live link.

---

## How it works

```
You open a GitHub Issue
  "Build me a CRM dashboard for tracking leads"
          ↓
GitHub Actions fires automatically
          ↓
Agent posts: "⏳ Generating your prototype..."
          ↓
Gemini generates:
  → A 3-5 bullet plan/spec
  → A complete, single-file HTML prototype
          ↓
HTML deployed to GitHub Pages
          ↓
Agent updates the comment:
  "✅ Your prototype is ready → https://you.github.io/repo/prototypes/1/"
```

Every prototype is also listed on a live index page at the root of your GitHub Pages site.

---

## Cost

Everything is free:

| Component | Free tier |
|---|---|
| Gemini 2.0 Flash | Free — [Google AI Studio](https://aistudio.google.com) |
| GitHub Actions | Free for public repos |
| GitHub Pages | Free |

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd prototype-agent
pip install -r requirements.txt
```

### 2. Get a Gemini API key

1. Go to **aistudio.google.com**
2. Sign in with Google → **Get API key**
3. Copy it (starts with `AIza...`) — no credit card needed

### 3. Add the GitHub secret

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | Your key from Google AI Studio |

### 4. Enable GitHub Pages

**Settings → Pages → Source: Deploy from a branch → Branch: `gh-pages` → Save**

The branch is created automatically on the first run.

### 5. Enable Actions

Go to the **Actions** tab and enable workflows if prompted.

---

## Usage

Open a GitHub Issue. Title = what you want. Body = details and requirements.

**Example:**

> **Title:** Sales pipeline dashboard
>
> **Body:**
> I need a Kanban-style board showing deals by stage: Lead, Proposal, Negotiation, Closed Won.
> Each card should show company name, deal value, and assigned rep.
> Include a summary bar at the top showing total value per stage and a win-rate chart.

The agent will comment on your issue within ~30 seconds with:
- A live link to the prototype
- A short plan of what was built
- A link to the raw HTML source
- A link to the index of all your prototypes

---

## Customize

### Use a smarter model

In your repo, go to **Settings → Variables → Actions** and add:

| Name | Value |
|---|---|
| `GEMINI_MODEL` | `gemini-1.5-pro` or `gemini-2.5-pro` |

### Change the design style or output format

Edit `SYSTEM_PROMPT` in `prototype_agent.py`. You can change the design system (e.g. force Material Design, use a specific colour palette), add constraints, or ask for different output (e.g. multi-page apps, data-heavy dashboards).

### Change the prompt structure

Edit the `generate_prototype` function in `prototype_agent.py` to add more context to what gets sent to Gemini — for example, you could inject a company brand guide or a list of components to use.

---

## Project structure

```
prototype-agent/
├── prototype_agent.py                  # Core agent logic
├── requirements.txt
├── .env.example
├── .github/workflows/
│   └── prototype-on-issue.yml          # Triggers on every new Issue
└── README.md
```

---

## License

MIT
