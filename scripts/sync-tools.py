#!/usr/bin/env python3
"""
Hourly sync: searches Reddit, X, Threads for role-specific content; updates
community insights and role instructions. Run via cron (0 * * * *) or GitHub Actions.
"""
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "lawagents-sync/1.0 (legal tools sync; https://github.com/lidvizion/lawagents)"

# Role slug -> search terms for Reddit/X/Threads
ROLE_SEARCH_TERMS = {
    "managing-partner": ["managing partner", "law firm leadership", "law firm CEO"],
    "equity-senior-partners": ["equity partner", "law firm partner", "law firm revenue"],
    "non-equity-junior-partners": ["non-equity partner", "junior partner", "law firm"],
    "associates": ["law firm associate", "associate attorney", "billable hours"],
    "of-counsel": ["of counsel", "law firm"],
    "contract-lawyers": ["contract attorney", "document review", "law firm contract"],
    "coo-firm-administrator": ["law firm COO", "firm administrator", "law firm operations"],
    "office-manager": ["law firm office manager", "legal office"],
    "billing-finance-manager": ["law firm billing", "legal billing", "time entry"],
    "finance-accounting-manager": ["law firm accounting", "legal finance", "law firm payroll"],
    "marketing-specialist": ["law firm marketing", "legal marketing", "law firm SEO"],
    "business-development-lead": ["law firm business development", "legal BD", "law firm clients"],
    "it-cybersecurity-lead": ["law firm cybersecurity", "legal IT", "law firm security"],
    "it-legaltech-specialist": ["legal tech", "law firm software", "Clio"],
    "compliance-risk-manager": ["law firm compliance", "legal compliance", "law firm risk"],
    "hr-recruiter": ["law firm hiring", "legal recruiting", "paralegal hiring"],
    "paralegal": ["paralegal", "legal assistant", "law firm paralegal"],
    "legal-assistant": ["legal assistant", "law firm admin"],
    "document-litigation-support-specialist": ["e-discovery", "litigation support", "document review"],
    "estate-trust-officer": ["trust officer", "estate administration", "probate"],
    "legal-intake-specialist": ["legal intake", "law firm intake", "client intake"],
    "legal-secretary": ["legal secretary", "law firm secretary"],
    "records-clerk-case-opener": ["case opener", "law firm filing", "records clerk"],
    "receptionist-front-desk": ["law firm receptionist", "legal front desk"],
}

# Subreddits to search (limit to avoid rate limits)
SUBREDDITS = ["LawFirm", "Lawyertalk", "paralegal"]

# Sync sources for tool checks
SYNC_SOURCES = [
    ("Clio G2", "https://www.g2.com/products/clio/reviews"),
    ("Harvey", "https://www.harvey.ai/"),
    ("GC.AI", "https://gc.ai/"),
]


def fetch_url(url: str, headers: dict | None = None) -> tuple[bool, str]:
    """Fetch URL and return (success, content_or_error)."""
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return True, r.read().decode()[:5000]
    except Exception as e:
        return False, str(e)


def get_reddit_token() -> str | None:
    """Get Reddit OAuth token. Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET env."""
    import os
    import base64
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return None
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={"User-Agent": USER_AGENT, "Authorization": "Basic " + base64.b64encode(f"{cid}:{secret}".encode()).decode()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode()).get("access_token")
    except Exception:
        return None


def search_reddit(subreddit: str, query: str, limit: int = 10, token: str | None = None) -> list[dict]:
    """Search Reddit subreddit. Returns list of {title, url, selftext, score}. Requires token from OAuth."""
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
                "selftext": (d.get("selftext") or "")[:500],
                "score": d.get("score", 0),
                "subreddit": subreddit,
            })
        return posts
    except (json.JSONDecodeError, KeyError):
        return []


def search_x(query: str, limit: int = 5) -> list[dict]:
    """Search X/Twitter. Requires X_API_KEY env. Returns [] if not configured."""
    import os
    token = os.environ.get("X_BEARER_TOKEN") or os.environ.get("X_API_KEY")
    if not token:
        return []
    # X API v2 search - requires Bearer token
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = urllib.parse.urlencode({"query": query, "max_results": min(limit, 10)})
    req = urllib.request.Request(f"{url}?{params}", headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            tweets = []
            for t in data.get("data", [])[:limit]:
                tweets.append({"text": t.get("text", "")[:280], "id": t.get("id", "")})
            return tweets
    except Exception:
        return []


def search_threads(query: str, limit: int = 5) -> list[dict]:
    """Search Threads. Requires THREADS_ACCESS_TOKEN env. Returns [] if not configured."""
    import os
    token = os.environ.get("THREADS_ACCESS_TOKEN")
    if not token:
        return []
    # Meta Threads API - basic search (if available)
    # Note: Threads API may have limited search; placeholder for when token is set
    url = "https://graph.threads.net/v1.0/search"
    params = urllib.parse.urlencode({"q": query, "access_token": token})
    try:
        with urllib.request.urlopen(f"{url}?{params}", timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get("data", [])[:limit]
    except Exception:
        return []


def gather_community_insights(role_slug: str, search_terms: list[str], reddit_token: str | None) -> dict:
    """Gather insights from Reddit, X, Threads for a role."""
    all_posts = []
    if reddit_token:
        for term in search_terms[:1]:
            for sub in SUBREDDITS[:2]:
                posts = search_reddit(sub, term, limit=5, token=reddit_token)
                all_posts.extend(posts)
                time.sleep(2)  # Reddit rate limit

    # Dedupe by URL
    seen = set()
    unique = []
    for p in sorted(all_posts, key=lambda x: -x.get("score", 0)):
        u = p.get("url", "")
        if u and u not in seen:
            seen.add(u)
            unique.append(p)

    x_results = []
    for term in search_terms[:1]:
        x_results.extend(search_x(f"{term} law firm", limit=3))

    threads_results = search_threads(f"{search_terms[0]} law firm", limit=3)

    return {
        "reddit": unique[:15],
        "x": x_results,
        "threads": threads_results,
    }


def write_community_insights(role_slug: str, insights: dict, updated_ts: str) -> None:
    """Write COMMUNITY_INSIGHTS.md for a role."""
    role_dir = REPO_ROOT / "roles" / role_slug
    if not role_dir.exists():
        return
    out = role_dir / "COMMUNITY_INSIGHTS.md"

    lines = [
        f"# Community Insights — {role_slug.replace('-', ' ').title()}",
        "",
        f"*Auto-updated hourly from Reddit, X, Threads. Last sync: {updated_ts} UTC*",
        "",
    ]
    if not insights.get("reddit") and not insights.get("x") and not insights.get("threads"):
        lines.extend([
            "## Setup",
            "",
            "To populate insights, add these secrets to the repo (Settings → Secrets):",
            "- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` — [Reddit API](https://www.reddit.com/prefs/apps)",
            "- `X_BEARER_TOKEN` — X API v2 (optional)",
            "- `THREADS_ACCESS_TOKEN` — Meta Threads API (optional)",
            "",
            "See [MAINTENANCE](../../MAINTENANCE.md) for details.",
            "",
        ])
    else:
        lines.extend(["## Reddit", ""])
    for p in insights.get("reddit", [])[:10]:
        lines.append(f"- **[{p['title'][:80]}...]({p['url']})** (r/{p.get('subreddit', '')}, score: {p.get('score', 0)})")
        if p.get("selftext"):
            snippet = p["selftext"][:200].replace("\n", " ")
            lines.append(f"  > {snippet}...")
        lines.append("")

    if insights.get("x"):
        lines.extend(["## X (Twitter)", ""])
        for t in insights["x"][:5]:
            lines.append(f"- {t.get('text', '')[:200]}...")
            lines.append("")

    if insights.get("threads"):
        lines.extend(["## Threads", ""])
        for t in insights["threads"][:5]:
            lines.append(f"- {str(t)[:200]}...")
            lines.append("")

    lines.extend([
        "",
        "---",
        "",
        "Use these insights to refine role instructions, tools, and pain points. See [MAINTENANCE](../../MAINTENANCE.md).",
    ])
    out.write_text("\n".join(lines))


def append_community_insights_ref(role_slug: str) -> bool:
    """Add 'Community Insights' section to role README if not present."""
    readme = REPO_ROOT / "roles" / role_slug / "README.md"
    insights_file = REPO_ROOT / "roles" / role_slug / "COMMUNITY_INSIGHTS.md"
    if not readme.exists() or not insights_file.exists():
        return False

    content = readme.read_text()
    if "COMMUNITY_INSIGHTS" in content or "Community Insights" in content:
        return False

    ref = "\n\n## Community Insights\n\n*Updated hourly from Reddit, X, Threads.* See [COMMUNITY_INSIGHTS.md](COMMUNITY_INSIGHTS.md).\n\n"
    for anchor in ["## Related Roles", "## See Also", "## Escalation Path"]:
        if anchor in content:
            content = content.replace(anchor, ref + anchor, 1)
            readme.write_text(content)
            return True
    return False


def check_sync_sources() -> dict:
    """Check key sync sources for accessibility."""
    results = {}
    for name, url in SYNC_SOURCES:
        ok, content = fetch_url(url)
        results[name] = {"ok": ok, "content_length": len(content)}
    return results


def update_agent_index(updated_ts: str) -> None:
    """Update docs/agent-index.json with new timestamp."""
    path = REPO_ROOT / "docs" / "agent-index.json"
    data = json.loads(path.read_text())
    data["updated"] = updated_ts
    data["last_community_sync"] = updated_ts
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_readme(updated_ts: str) -> None:
    """Update README with last synced timestamp."""
    path = REPO_ROOT / "README.md"
    content = path.read_text()
    pattern = r"\*Last synced: .+\*"
    replacement = f"*Last synced: {updated_ts} UTC (Reddit, X, Threads per role)*"
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        content = content.rstrip() + f"\n\n{replacement}\n"
    path.write_text(content)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"Sync run at {now} UTC")

    # 1. Check sync sources
    sync_results = check_sync_sources()
    for name, r in sync_results.items():
        status = "ok" if r["ok"] else "fail"
        print(f"  {name}: {status}")

    # 2. Search Reddit/X/Threads per role; write COMMUNITY_INSIGHTS.md
    reddit_token = get_reddit_token()
    roles_updated = 0
    for role_slug, terms in ROLE_SEARCH_TERMS.items():
        insights = gather_community_insights(role_slug, terms, reddit_token)
        write_community_insights(role_slug, insights, now)
        if insights.get("reddit") or insights.get("x") or insights.get("threads"):
            roles_updated += 1
        append_community_insights_ref(role_slug)

    print(f"  Community insights: {roles_updated} roles updated")

    # 3. Update agent-index and README
    update_agent_index(now)
    update_readme(now)
    print("Updated agent-index.json and README")

    return 0


if __name__ == "__main__":
    sys.exit(main())
