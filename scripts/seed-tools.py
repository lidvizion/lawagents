#!/usr/bin/env python3
"""
Seed MongoDB tools and integrations from agent-index.json and catalog.
Sets has_mcp flag for tools with MCP support.
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Tools with known MCP support
HAS_MCP_SLUGS = {"zapier-clio-mcp", "buffer", "hootsuite"}

# Curated API/MCP tools to ensure are in DB
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


def main() -> int:
    from libs.db import get_tools_collection, get_integrations_collection, ensure_indexes

    coll = get_tools_collection()
    if coll is None:
        print("MONGODB_URI not set. Skipping seed.")
        return 1

    ensure_indexes()

    # Load from agent-index
    index_path = REPO_ROOT / "docs" / "agent-index.json"
    data = json.loads(index_path.read_text())
    items = data.get("tools", {}).get("items", [])

    for item in items:
        slug = item.get("slug", "")
        if not slug:
            continue
        doc = {
            "slug": slug,
            "name": item.get("name", ""),
            "category": item.get("category", "other"),
            "use_when": item.get("use_when", ""),
            "path": item.get("path", ""),
            "score": item.get("score"),
            "has_api": slug not in {"zapier-clio-mcp"} or True,  # Zapier has API
            "has_mcp": slug in HAS_MCP_SLUGS,
            "last_synced": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        coll.update_one({"slug": slug}, {"$set": doc}, upsert=True)

    # Add curated API tools
    for tool in CURATED_TOOLS:
        coll.update_one(
            {"slug": tool["slug"]},
            {"$set": {**tool, "last_synced": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}},
            upsert=True,
        )

    print(f"Seeded {len(items) + len(CURATED_TOOLS)} tools")

    # Seed integrations
    int_coll = get_integrations_collection()
    if int_coll is not None:
        integrations = [
            {"slug": "zapier-clio-mcp", "name": "Zapier Clio MCP", "type": "mcp", "tool_slug": "clio", "url": "https://zapier.com/mcp/clio"},
            {"slug": "zapier-buffer-mcp", "name": "Zapier Buffer MCP", "type": "mcp", "tool_slug": "buffer", "url": "https://zapier.com/mcp/buffer"},
            {"slug": "zapier-hootsuite-mcp", "name": "Zapier Hootsuite MCP", "type": "mcp", "tool_slug": "hootsuite", "url": "https://zapier.com/mcp/hootsuite"},
        ]
        for i in integrations:
            int_coll.update_one({"slug": i["slug"]}, {"$set": i}, upsert=True)
        print(f"Seeded {len(integrations)} integrations")

    return 0


if __name__ == "__main__":
    sys.exit(main())
