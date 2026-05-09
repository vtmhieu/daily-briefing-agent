# Prototype Agent

Turn a plain-English requirement into a live, clickable UI prototype in ~30 seconds — free, no servers, fully automated.

**Portal:** `https://vtmhieu.github.io/daily-briefing-agent/`

---

## How it works

```
You open the portal and type your requirement
          ↓
Portal creates a GitHub Issue automatically
          ↓
Agent posts: "⏳ Generating your prototype..."
          ↓
Gemini generates:
  → A 3-5 bullet plan/spec
  → A complete, single-file HTML prototype
          ↓
HTML deployed to GitHub Pages
          ↓
Agent updates the comment with the live link
          ↓
Portal detects the result and shows you the link
```

Every prototype is listed in the portal under **Past prototypes**.

---

## Cost

Everything is free:

| Component | Free tier |
|---|---|
| Gemini 2.0 Flash Lite | Free — [Google AI Studio](https://aistudio.google.com) |
| GitHub Actions | Free for public repos |
| GitHub Pages | Free |

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
2. Sign in with Google → **Get API key** → **Create API key in new project**
3. Copy the key (starts with `AIza...`) — no credit card needed

### 3. Add the GitHub secret

**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | Your key from Google AI Studio |

### 4. Enable GitHub Pages

**Settings → Pages → Source: Deploy from a branch → Branch: `gh-pages` → Save**

The `gh-pages` branch is created automatically on the first prototype run.

### 5. Enable Actions

Go to the **Actions** tab and enable workflows if prompted.

### 6. Deploy the portal

Go to **Actions → Deploy Portal → Run workflow** to push the portal to GitHub Pages for the first time.

---

## Usage

Open your portal at `https://<your-username>.github.io/<repo-name>/`

1. **First visit:** paste a GitHub personal access token ([create one here](https://github.com/settings/tokens/new?scopes=public_repo&description=Prototype+Agent) with `public_repo` scope) — saved in your browser, never leaves it
2. Type a title and optional details for what you want to build
3. Click **Generate Prototype**
4. The portal shows a live counter while the agent works (~30s)
5. When done, click **Open prototype →** to see it in your browser

**Example input:**

> **Title:** Sales pipeline dashboard
>
> **Details:** Kanban board with stages: Lead, Proposal, Negotiation, Closed Won. Cards show company, deal value, assigned rep. Summary bar at top with total value per stage and a win-rate donut chart.

---

## Customize

### Use a smarter model

In **Settings → Variables → Actions**, add:

| Name | Value |
|---|---|
| `GEMINI_MODEL` | `gemini-2.0-flash` or `gemini-1.5-pro` |

### Change the design style

Edit `SYSTEM_PROMPT` in `prototype_agent.py` to change the design language, force a specific component library, or add brand constraints.

### Change the prompt format

Edit `generate_prototype()` in `prototype_agent.py` to inject additional context into every Gemini call.

---

## Project structure

```
daily-briefing-agent/
├── prototype_agent.py                  # Core agent — generates + deploys prototypes
├── deploy_portal.py                    # Deploys portal/index.html to gh-pages
├── portal/
│   └── index.html                      # Web portal UI
├── requirements.txt
├── .env.example
├── .github/workflows/
│   ├── prototype-on-issue.yml          # Triggers on every new GitHub Issue
│   └── deploy-portal.yml              # Deploys portal on push to main
└── README.md
```

---

## License

MIT
