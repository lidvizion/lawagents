#!/usr/bin/env python3
"""
Hourly sync script: searches for new information and updates README.
Run via: cron (0 * * * *) or GitHub Actions.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def fetch_url(url: str) -> tuple[bool, str]:
    """Fetch URL and return (success, content_or_error)."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10", url],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, result.stdout[:2000] if result.stdout else ""
        return False, result.stderr or "Unknown error"
    except FileNotFoundError:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as r:
                return True, r.read().decode()[:2000]
        except Exception as e:
            return False, str(e)


def check_sync_sources() -> dict:
    """Check key sync sources for accessibility and extract any updates."""
    sources = [
        ("Clio G2", "https://www.g2.com/products/clio/reviews"),
        ("Harvey", "https://www.harvey.ai/"),
        ("GC.AI", "https://gc.ai/"),
    ]
    results = {}
    for name, url in sources:
        ok, content = fetch_url(url)
        results[name] = {"ok": ok, "content_length": len(content)}
        if ok and content:
            # Simple heuristic: look for rating-like patterns
            if "stars" in content.lower() or "rating" in content.lower():
                results[name]["has_rating"] = True
    return results


def update_agent_index(updated_ts: str) -> None:
    """Update docs/agent-index.json with new timestamp."""
    path = REPO_ROOT / "docs" / "agent-index.json"
    data = json.loads(path.read_text())
    data["updated"] = updated_ts
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_readme(updated_ts: str, sync_results: dict) -> None:
    """Update README with last synced timestamp."""
    path = REPO_ROOT / "README.md"
    content = path.read_text()

    # Pattern: *Last synced: ...* or *Last synced: (hourly by cron)*
    pattern = r"\*Last synced: .+\*"
    replacement = f"*Last synced: {updated_ts} UTC*"

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        content = content.rstrip() + f"\n\n{replacement}\n"

    path.write_text(content)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"Sync run at {now} UTC")

    sync_results = check_sync_sources()
    for name, r in sync_results.items():
        status = "ok" if r["ok"] else "fail"
        print(f"  {name}: {status} (len={r.get('content_length', 0)})")

    update_agent_index(now)
    update_readme(now, sync_results)
    print("Updated agent-index.json and README")

    return 0


if __name__ == "__main__":
    sys.exit(main())
