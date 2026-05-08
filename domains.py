"""
Domain configuration.
Add, remove, or edit domains here — the agent will pick them up automatically.
"""

DOMAINS = {
    "tech_ai": {
        "name": "Tech & AI",
        "emoji": "🤖",
        "focus": (
            "AI model releases, major tech company news, startup launches, "
            "developer tools, and significant research papers. "
            "Prioritize stories from Hacker News, TechCrunch, The Verge, and arxiv."
        ),
    },
    "finance": {
        "name": "Finance & Markets",
        "emoji": "💰",
        "focus": (
            "Major market movements, central bank decisions, earnings reports "
            "from S&P 500 companies, and macroeconomic developments. "
            "Prioritize Bloomberg, Reuters, FT, and WSJ."
        ),
    },
    "startups_vc": {
        "name": "Startups & VC",
        "emoji": "🚀",
        "focus": (
            "Funding rounds (Series A and above), notable acquisitions, "
            "YC batch news, unicorn updates, and venture capital trends. "
            "Prioritize Crunchbase, TechCrunch, The Information, and Pitchbook."
        ),
    },
    "crypto": {
        "name": "Crypto",
        "emoji": "₿",
        "focus": (
            "BTC and ETH price movements, major altcoin news, regulatory updates, "
            "DeFi/NFT trends, and exchange news. "
            "Prioritize CoinDesk, The Block, and CryptoPanic."
        ),
    },
}
