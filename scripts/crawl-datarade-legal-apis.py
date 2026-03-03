#!/usr/bin/env python3
"""
Crawl dataRade.ai legal APIs and update MongoDB.

dataRade does not expose a public API; the site is behind Cloudflare.
We use OpenAI (knowledge + optional web search) to discover legal APIs
from dataRade and other sources, then upsert into MongoDB.

Usage:
  export MONGODB_URI="mongodb://..."
  export OPENAI_API_KEY="sk-..."
  python scripts/crawl-datarade-legal-apis.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Curated legal APIs from dataRade and known sources (fallback when no OpenAI)
CURATED_LEGAL_APIS = [
    {"name": "UniCourt", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-providers/unicourt/data-products"},
    {"name": "Bloomberg Law Dockets API", "provider": "Bloomberg", "category": "court-data", "url": "https://pro.bloomberglaw.com/products/court-dockets-search/enterprise-dockets-api-solution/"},
    {"name": "LegiScan API", "provider": "LegiScan", "category": "legislative", "url": "https://legiscan.com/legiscan"},
    {"name": "OpenLaws API", "provider": "OpenLaws", "category": "legislative", "url": "https://openlaws.us/api/"},
    {"name": "TrustFoundry AI", "provider": "TrustFoundry", "category": "legal-ai", "url": "https://trustfoundry.ai/"},
    {"name": "PACER API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/pacer-api-unicourt"},
    {"name": "Court Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/court-data-api-unicourt"},
    {"name": "Attorney Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/attorney-data-api-unicourt"},
    {"name": "Law Firm Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/law-firm-data-api-unicourt"},
    {"name": "Judge Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/judge-data-api-unicourt"},
    {"name": "Legal Analytics API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/data-products/legal-analytics-api-unicourt"},
    {"name": "APISCRAPY Legal Data", "provider": "APISCRAPY", "category": "court-data", "url": "https://datarade.ai/search/products/legal-apis"},
    {"name": "Grepsr Legal Data", "provider": "Grepsr", "category": "court-data", "url": "https://datarade.ai/search/products/legal-apis"},
    {"name": "InfoTrack", "provider": "InfoTrack", "category": "court-filing", "url": "https://www.infotrack.com/"},
    {"name": "LexisNexis API", "provider": "LexisNexis", "category": "legal-research", "url": "https://www.lexisnexis.com/"},
    {"name": "Westlaw API", "provider": "Thomson Reuters", "category": "legal-research", "url": "https://legal.thomsonreuters.com/"},
]


def slugify(name: str) -> str:
    """Convert name to slug for MongoDB."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "unknown"


def get_openai_legal_apis() -> list[dict]:
    """Use OpenAI to discover legal APIs from dataRade and other sources."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not api_key:
        return []

    try:
        from openai import OpenAI
    except ImportError:
        return []

    client = OpenAI(api_key=api_key)

    prompt = """You are helping build a catalog of legal APIs for law firms.

List 50+ legal APIs and data products that appear on dataRade.ai (datarade.ai/search/products/legal-apis) or are commonly used by law firms.

For each API, provide:
- name: Product/API name
- provider: Company or provider name
- category: One of court-data, legislative, legal-research, legal-ai, e-discovery, practice-management, trademark-ip, compliance
- url: Best URL (datarade product page, vendor docs, or API docs)
- description: One sentence on what it does (optional)

Return a JSON array of objects. Example:
[{"name": "UniCourt Court Data API", "provider": "UniCourt", "category": "court-data", "url": "https://datarade.ai/...", "description": "..."}]

Include: UniCourt, Bloomberg Law, LegiScan, OpenLaws, PACER, court data, legislative, trademark, legal research, e-discovery, and any other legal APIs you know from dataRade or legal tech."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.choices[0].message.content or "").strip()

        # Extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            arr = json.loads(text[start:end])
            if isinstance(arr, list):
                return arr
    except Exception as e:
        print(f"OpenAI error: {e}", file=sys.stderr)

    return []


def tool_doc(api: dict, source: str = "datarade") -> dict:
    """Build tool document for MongoDB."""
    name = api.get("name", "Unknown")
    slug = slugify(name)
    return {
        "slug": slug,
        "name": name,
        "category": api.get("category", "legal-api"),
        "provider": api.get("provider", ""),
        "use_when": api.get("description", f"Legal API: {name}"),
        "url": api.get("url", ""),
        "source": source,
        "has_mcp": False,  # Will be updated by weekly sync if MCP found
        "has_api": True,
        "last_synced": datetime.now(timezone.utc).isoformat(),
        "sync_sources": [api.get("url", "https://datarade.ai/search/products/legal-apis")],
    }


def main() -> int:
    print("Crawl dataRade legal APIs → MongoDB")
    print("-" * 50)

    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        print("ERROR: MONGODB_URI is required", file=sys.stderr)
        return 1

    # Discover APIs
    apis: list[dict] = []
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY"):
        print("Using OpenAI to discover legal APIs...")
        apis = get_openai_legal_apis()
        if apis:
            print(f"  Found {len(apis)} APIs via OpenAI")
    else:
        print("OPENAI_API_KEY not set; using curated list only")

    # Merge with curated (dedupe by name)
    seen_names = {a["name"].lower() for a in apis}
    for c in CURATED_LEGAL_APIS:
        if c["name"].lower() not in seen_names:
            apis.append(c)
            seen_names.add(c["name"].lower())

    if not apis:
        apis = CURATED_LEGAL_APIS
        print(f"Using {len(apis)} curated APIs")

    # Connect to MongoDB
    try:
        from libs.db import get_tools_collection, ensure_indexes
    except ImportError:
        sys.path.insert(0, str(REPO_ROOT))
        from libs.db import get_tools_collection, ensure_indexes

    ensure_indexes()
    tools = get_tools_collection()

    # Upsert
    upserted = 0
    for api in apis:
        doc = tool_doc(api)
        slug = doc["slug"]
        result = tools.update_one(
            {"slug": slug},
            {"$set": doc},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            upserted += 1

    print(f"Upserted {upserted} tools to MongoDB")
    print(f"Total in catalog: {tools.count_documents({'source': 'datarade'})} from dataRade")

    # Write JSON index for docs
    index_path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_data = {
        "source": "datarade",
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "count": len(apis),
        "apis": [{"name": a.get("name"), "provider": a.get("provider"), "category": a.get("category"), "url": a.get("url")} for a in apis],
    }
    index_path.write_text(json.dumps(index_data, indent=2))
    print(f"Wrote {index_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
