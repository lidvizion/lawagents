#!/usr/bin/env python3
"""
Search for new legal tools: Reddit, directories, review platforms.
Outputs to docs/tools/TOOL-DISCOVERIES.md for manual review.
Run via cron (0 6 * * *) or GitHub Actions (daily).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "tools" / "TOOL-DISCOVERIES.md"
USER_AGENT = "lawagents-search/1.0 (legal tools discovery; https://github.com/lidvizion/lawagents)"

# Reddit search queries for discovering new tools
REDDIT_SEARCH_QUERIES = [
    "legal AI",
    "law firm software",
    "legal tech",
    "practice management software",
    "contract review AI",
    "e-discovery software",
    "Clio alternative",
]

# Subreddits to search
SUBREDDITS = ["LawFirm", "Lawyertalk", "paralegal", "ediscovery", "LegalTech"]

# Directories / review platforms to monitor (fetch for link discovery)
DIRECTORIES = [
    ("Law Leaders - Top Legal AI Agents", "https://lawleaders.com/the-top-legal-ai-agents-used-by-law-firms-today/"),
    ("Sana Labs - Enterprise Legal AI", "https://sanalabs.com/agents-blog/enterprise-legal-ai-agents-law-firms-2025"),
    ("G2 Legal Practice Management", "https://www.g2.com/categories/legal-practice-management-software"),
]

# Reddit threads to monitor (from RESEARCH-SOURCES / SYNC-SOURCES)
REDDIT_THREADS = [
    ("r/LawFirm - experimented with new", "https://www.reddit.com/r/LawFirm/comments/1pf73ov/has_anyone_experimented_with_the_new/"),
]


def get_reddit_token() -> str | None:
    """Get Reddit OAuth token. Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env."""
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return None
    import base64
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Authorization": "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get("access_token")
    except Exception:
        return None


def fetch_url(url: str, headers: dict | None = None) -> tuple[bool, str]:
    """Fetch URL and return (success, content_or_error)."""
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return True, r.read().decode()[:15000]
    except Exception as e:
        return False, str(e)


def search_reddit(subreddit: str, query: str, limit: int = 5, token: str | None = None) -> list[dict]:
    """Search Reddit subreddit. Returns list of {title, url, selftext, score}."""
    q = urllib.parse.quote(query)
    url = f"https://oauth.reddit.com/r/{subreddit}/search.json?q={q}&restrict_sr=on&sort=relevance&limit={limit}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    ok, content = fetch_url(url, headers)
    if not ok or not content.strip():
        return []
    try:
        data = json.loads(content)
        posts = []
        for child in data.get("data", {}).get("children", [])[:limit]:
            d = child.get("data", {})
            posts.append({
                "title": d.get("title", "")[:200],
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "selftext": (d.get("selftext") or "")[:300],
                "score": d.get("score", 0),
                "subreddit": subreddit,
                "query": query,
            })
        return posts
    except (json.JSONDecodeError, KeyError):
        return []


def extract_tool_mentions(text: str) -> list[str]:
    """Extract potential tool names from text (simple heuristic)."""
    # Known tools to ignore (already in catalog)
    known = {"clio", "harvey", "filevine", "mycase", "casepeer", "cloudlex", "everlaw",
             "gc.ai", "crosby", "lawhive", "zapier", "buffer", "hootsuite", "scrapling"}
    words = text.replace(",", " ").replace(".", " ").split()
    candidates = []
    for i, w in enumerate(words):
        wl = w.lower()
        if wl in known or len(wl) < 4:
            continue
        # Capitalized words that might be product names
        if w[0].isupper() and w.isalnum():
            candidates.append(w)
    return list(dict.fromkeys(candidates))[:10]


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"Tool search run at {now} UTC")

    all_reddit = []
    token = get_reddit_token()
    if not token:
        print("  Reddit: skipped (set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET for Reddit search)")

    for query in REDDIT_SEARCH_QUERIES[:4]:
        for sub in SUBREDDITS[:3]:
            posts = search_reddit(sub, query, limit=3, token=token)
            for p in posts:
                p["mentions"] = extract_tool_mentions(p.get("title", "") + " " + p.get("selftext", ""))
            all_reddit.extend(posts)
            if token:
                time.sleep(2)

    # Dedupe by URL
    seen = set()
    unique_reddit = []
    for p in sorted(all_reddit, key=lambda x: -x.get("score", 0)):
        u = p.get("url", "")
        if u and u not in seen:
            seen.add(u)
            unique_reddit.append(p)

    # Check directories (accessibility)
    dir_status = []
    for name, url in DIRECTORIES:
        ok, _ = fetch_url(url)
        dir_status.append((name, url, "ok" if ok else "fail"))

    # Build output
    lines = [
        "# Tool Discoveries",
        "",
        f"*Auto-generated from Reddit search and directory checks. Last run: {now} UTC*",
        "",
        "Review these findings and add promising tools to [SYNC-SOURCES.md](SYNC-SOURCES.md) and the [catalog](catalog/).",
        "",
        "---",
        "",
        "## Reddit (potential new tools)",
        "",
    ]
    if not unique_reddit:
        lines.extend([
            "No Reddit results. Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to repo Secrets.",
            "",
        ])
    else:
        for p in unique_reddit[:25]:
            lines.append(f"- **[{p['title'][:80]}]({p['url']})** (r/{p.get('subreddit', '')}, score: {p.get('score', 0)})")
            if p.get("mentions"):
                lines.append(f"  - Mentions: {', '.join(p['mentions'][:5])}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## Directories to monitor",
        "",
        "| Source | URL | Status |",
        "|--------|-----|--------|",
    ])
    for name, url, status in dir_status:
        lines.append(f"| {name} | {url} | {status} |")
    lines.append("")

    lines.extend([
        "---",
        "",
        "## Reddit threads to monitor",
        "",
    ])
    for name, url in REDDIT_THREADS:
        lines.append(f"- [{name}]({url})")
    lines.append("")

    lines.extend([
        "---",
        "",
        "See [scripts/README.md](../../scripts/README.md) for running this search.",
        "",
    ])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines))
    print(f"  Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
