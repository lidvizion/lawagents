#!/usr/bin/env python3
"""
Seed MongoDB tools and integrations from legal-apis-index.json, agent-index.json,
and curated API entries. Sets has_mcp for known MCP-capable tools.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from libs.db import ensure_indexes, get_integrations_collection, get_tools_collection

HAS_MCP_SLUGS = frozenset({"zapier-clio-mcp", "buffer", "hootsuite"})

CURATED_TOOLS = [
    {
        "slug": "bloomberg-law-dockets-api",
        "name": "Bloomberg Law Enterprise Dockets API",
        "category": "court-data",
        "use_when": "Enterprise court docket search; federal and state court records",
        "has_api": True,
        "has_mcp": False,
        "url": "https://pro.bloomberglaw.com/products/court-dockets-search/enterprise-dockets-api-solution/",
    },
    {
        "slug": "trustfoundry-ai",
        "name": "TrustFoundry AI",
        "category": "legal-ai",
        "use_when": "Legal research; AI search; solo/small firm affordability",
        "has_api": True,
        "has_mcp": False,
        "url": "https://trustfoundry.ai/",
    },
    {
        "slug": "legiscan",
        "name": "LegiScan API",
        "category": "legislative-api",
        "use_when": "Legislative tracking; bill data; all 50 states + Congress",
        "has_api": True,
        "has_mcp": False,
        "url": "https://legiscan.com/legiscan",
    },
    {
        "slug": "openlaws-api",
        "name": "OpenLaws API",
        "category": "legislative-api",
        "use_when": "Statutes, regulations, case law; citation validation; RAG/LLM",
        "has_api": True,
        "has_mcp": False,
        "url": "https://openlaws.us/api/",
    },
]


def load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def main() -> int:
    tools_coll = get_tools_collection()
    if tools_coll is None:
        print("MONGODB_URI not set or MongoDB unavailable.")
        return 1

    ensure_indexes()

    tools_list: list[dict] = []

    apis_path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    apis_data = load_json(apis_path)
    if isinstance(apis_data, dict):
        tools_list.extend(apis_data.get("tools") or apis_data.get("apis") or [])

    agent_path = REPO_ROOT / "docs" / "agent-index.json"
    agent_data = load_json(agent_path)
    if isinstance(agent_data, dict):
        for t in agent_data.get("tools", {}).get("items", []):
            slug = t.get("slug")
            if not slug:
                continue
            tools_list.append(
                {
                    "slug": slug,
                    "name": t.get("name", slug),
                    "category": t.get("category", "legal-tech"),
                    "use_when": t.get("use_when", ""),
                    "path": t.get("path", ""),
                    "score": t.get("score"),
                    "url": t.get("url", ""),
                }
            )

    by_slug: dict[str, dict] = {}
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
            "has_api": t.get("has_api", True),
            "has_mcp": t.get("has_mcp", slug in HAS_MCP_SLUGS),
            "provider": t.get("provider", ""),
            "source": t.get("source", "catalog"),
            "last_synced": datetime.now(timezone.utc).isoformat(),
        }

    for tool in CURATED_TOOLS:
        slug = tool["slug"]
        prev = by_slug.get(slug, {})
        by_slug[slug] = {
            **prev,
            **tool,
            "has_mcp": tool.get("has_mcp", False),
            "last_synced": datetime.now(timezone.utc).isoformat(),
        }

    for slug, doc in by_slug.items():
        doc["has_mcp"] = doc.get("has_mcp", False) or slug in HAS_MCP_SLUGS
        tools_coll.update_one({"slug": slug}, {"$set": doc}, upsert=True)

    print(f"Seeded {len(by_slug)} tools to MongoDB")

    int_coll = get_integrations_collection()
    if int_coll is not None:
        integrations = [
            {
                "slug": "zapier-clio-mcp",
                "name": "Zapier Clio MCP",
                "type": "mcp",
                "tool_slug": "clio",
                "url": "https://zapier.com/mcp/clio",
                "auth_type": "oauth",
                "capabilities": ["create_matter", "create_task", "create_contact"],
            },
            {
                "slug": "zapier-buffer-mcp",
                "name": "Zapier Buffer MCP",
                "type": "mcp",
                "tool_slug": "buffer",
                "url": "https://zapier.com/mcp/buffer",
                "auth_type": "oauth",
                "capabilities": ["schedule_post"],
            },
            {
                "slug": "zapier-hootsuite-mcp",
                "name": "Zapier Hootsuite MCP",
                "type": "mcp",
                "tool_slug": "hootsuite",
                "url": "https://zapier.com/mcp/hootsuite",
                "auth_type": "oauth",
                "capabilities": ["schedule_post", "unified_inbox"],
            },
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
