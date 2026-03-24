#!/usr/bin/env python3
"""
Seed MongoDB tools and integrations from legal-apis-index.json and agent-index.json.
Run after crawl-datarade-legal-apis.py to sync DB with catalog.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from libs.db import (
    ensure_indexes,
    get_integrations_collection,
    get_tools_collection,
)


def load_json(path: Path) -> dict | list:
    """Load JSON file."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def main() -> int:
    tools_coll = get_tools_collection()
    if tools_coll is None:
        print("MONGODB_URI not set or MongoDB unavailable.")
        sys.exit(1)

    ensure_indexes()

    # 1. Load from legal-apis-index.json (crawl output)
    apis_path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    apis_data = load_json(apis_path)
    tools_list = apis_data.get("tools", []) if isinstance(apis_data, dict) else []

    # 2. Load from agent-index.json (curated catalog)
    agent_path = REPO_ROOT / "docs" / "agent-index.json"
    agent_data = load_json(agent_path)
    if isinstance(agent_data, dict):
        items = agent_data.get("tools", {}).get("items", [])
        for t in items:
            slug = t.get("slug")
            if not slug:
                continue
            tools_list.append({
                "slug": slug,
                "name": t.get("name", slug),
                "category": t.get("category", "legal-tech"),
                "use_when": t.get("use_when", ""),
                "path": t.get("path", ""),
                "score": t.get("score"),
                "url": "",
            })

    # Dedupe by slug (later wins)
    by_slug: dict = {}
    for t in tools_list:
        slug = t.get("slug") or ""
        if not slug:
            continue
        by_slug[slug] = {
            "slug": slug,
            "name": t.get("name", slug),
            "category": t.get("category", "legal-tech"),
            "use_when": t.get("use_when", ""),
            "url": t.get("url", ""),
            "path": t.get("path", ""),
            "score": t.get("score"),
            "has_api": t.get("has_api", False),
            "has_mcp": t.get("has_mcp", False),
            "provider": t.get("provider", ""),
            "last_synced": datetime.now(timezone.utc).isoformat(),
        }

    # Upsert to MongoDB
    count = 0
    for slug, doc in by_slug.items():
        tools_coll.update_one(
            {"slug": slug},
            {"$set": doc},
            upsert=True,
        )
        count += 1

    print(f"Seeded {count} tools to MongoDB")

    # 3. Seed integrations (MCP/API connectors)
    int_coll = get_integrations_collection()
    if int_coll is not None:
        integrations = [
            {"slug": "zapier-clio-mcp", "name": "Zapier Clio MCP", "type": "mcp", "tool_slug": "clio", "url": "https://zapier.com", "auth_type": "oauth", "capabilities": ["create_matter", "create_task", "create_contact"]},
            {"slug": "buffer-mcp", "name": "Buffer MCP", "type": "mcp", "tool_slug": "buffer", "url": "https://buffer.com", "auth_type": "oauth", "capabilities": ["schedule_post"]},
            {"slug": "hootsuite-mcp", "name": "Hootsuite MCP", "type": "mcp", "tool_slug": "hootsuite", "url": "https://hootsuite.com", "auth_type": "oauth", "capabilities": ["schedule_post", "unified_inbox"]},
        ]
        for i in integrations:
            int_coll.update_one(
                {"slug": i["slug"]},
                {"$set": {**i, "last_synced": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
        print(f"Seeded {len(integrations)} integrations")

    return 0


if __name__ == "__main__":
    sys.exit(main())
