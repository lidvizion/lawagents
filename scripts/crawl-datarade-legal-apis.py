#!/usr/bin/env python3
"""
Crawl and index legal APIs from dataRade (https://datarade.ai/search/products/legal-apis).
Uses OpenAI to discover and extract legal API products. Outputs to docs/tools/legal-apis-index.json
and optionally updates MongoDB.
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def get_openai_client():
    """Lazy import OpenAI client."""
    try:
        from openai import OpenAI
        return OpenAI()
    except ImportError:
        return None


def get_static_legal_apis() -> list[dict]:
    """Fallback: curated list from dataRade and known sources when OpenAI unavailable."""
    return [
        {"name": "UniCourt Court Data API", "slug": "unicourt-court-data", "provider": "UniCourt", "category": "court-data", "use_when": "USA court records, AI-normalized", "url": "https://datarade.ai/data-providers/unicourt/data-products", "has_api": True, "has_mcp": False},
        {"name": "UniCourt Law Firm Data API", "slug": "unicourt-law-firm", "provider": "UniCourt", "category": "law-firm-data", "use_when": "USA law firm legal data", "url": "https://datarade.ai/data-products/law-firm-data-api-unicourt", "has_api": True, "has_mcp": False},
        {"name": "UniCourt PACER API", "slug": "unicourt-pacer", "provider": "UniCourt", "category": "court-data", "use_when": "PACER legal data", "url": "https://datarade.ai/data-providers/unicourt/data-products", "has_api": True, "has_mcp": False},
        {"name": "APISCRAPY Court Record Data", "slug": "apiscrapy-court", "provider": "APISCRAPY", "category": "court-data", "use_when": "Federal and state court records, 10M+ records", "url": "https://datarade.ai/search/products/legal-apis", "has_api": True, "has_mcp": False},
        {"name": "Grepsr Legal Data", "slug": "grepsr-legal", "provider": "Grepsr", "category": "court-data", "use_when": "Court cases, lawyers, law firms; global coverage", "url": "https://datarade.ai/data-products/legal-judicial-court-data-grepsr-grepsr", "has_api": True, "has_mcp": False},
        {"name": "Bloomberg Law Enterprise Dockets API", "slug": "bloomberg-law-dockets-api", "provider": "Bloomberg", "category": "court-data", "use_when": "Enterprise court docket search", "url": "https://pro.bloomberglaw.com/products/court-dockets-search/enterprise-dockets-api-solution/", "has_api": True, "has_mcp": False},
        {"name": "LegiScan API", "slug": "legiscan", "provider": "LegiScan", "category": "legislative", "use_when": "Legislative tracking; all 50 states + Congress", "url": "https://legiscan.com/legiscan", "has_api": True, "has_mcp": False},
        {"name": "OpenLaws API", "slug": "openlaws-api", "provider": "OpenLaws", "category": "legislative", "use_when": "Statutes, regulations, case law; RAG/LLM", "url": "https://openlaws.us/api/", "has_api": True, "has_mcp": False},
        {"name": "TrustFoundry AI", "slug": "trustfoundry-ai", "provider": "TrustFoundry", "category": "legal-research", "use_when": "Legal research; AI search; solo/small firm", "url": "https://trustfoundry.ai/", "has_api": True, "has_mcp": False},
        {"name": "Success.ai Legal APIs", "slug": "success-ai-legal", "provider": "Success.ai", "category": "legal-research", "use_when": "Legal data APIs", "url": "https://datarade.ai/search/products/legal-apis", "has_api": True, "has_mcp": False},
        {"name": "Rightsify Legal Data", "slug": "rightsify-legal", "provider": "Rightsify", "category": "legal-research", "use_when": "Legal data", "url": "https://datarade.ai/search/products/legal-apis", "has_api": True, "has_mcp": False},
        {"name": "Nubela Legal APIs", "slug": "nubela-legal", "provider": "Nubela", "category": "legal-research", "use_when": "Legal data", "url": "https://datarade.ai/search/products/legal-apis", "has_api": True, "has_mcp": False},
        {"name": "Oxylabs Legal Data", "slug": "oxylabs-legal", "provider": "Oxylabs", "category": "legal-research", "use_when": "Legal data scraping", "url": "https://datarade.ai/search/products/legal-apis", "has_api": True, "has_mcp": False},
        {"name": "CTOS Basis Litigation", "slug": "ctos-basis-litigation", "provider": "CTOS Basis", "category": "litigation", "use_when": "Litigation data", "url": "https://datarade.ai/search/products/litigation-apis", "has_api": True, "has_mcp": False},
        {"name": "Moat Legal Data", "slug": "moat-legal", "provider": "Moat", "category": "litigation", "use_when": "Litigation APIs", "url": "https://datarade.ai/search/products/litigation-apis", "has_api": True, "has_mcp": False},
    ]


def discover_legal_apis_via_openai() -> list[dict]:
    """Use OpenAI to generate a comprehensive list of legal APIs from dataRade and known sources."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Using static list. Add OPENAI_API_KEY to .env for full crawl.")
        return get_static_legal_apis()

    client = get_openai_client()
    if not client:
        return get_static_legal_apis()

    prompt = """You are a legal tech researcher. Generate a comprehensive list of legal APIs and data products.

Source: https://datarade.ai/search/products/legal-apis lists 100+ legal APIs. Also include:
- Court data APIs (UniCourt, APISCRAPY, Grepsr, PACER, etc.)
- Legislative APIs (LegiScan, OpenLaws, etc.)
- Law firm / attorney data APIs
- Litigation APIs
- Legal research APIs
- Compliance / regulatory APIs

For each API, provide:
- name: Product/API name
- slug: lowercase-hyphenated identifier
- provider: Company/provider name
- category: one of court-data, legislative, law-firm-data, litigation, legal-research, compliance, other
- use_when: One sentence when to use
- url: dataRade or vendor URL if known
- has_api: true
- has_mcp: false (unless you know it has MCP/Model Context Protocol)

Return a JSON array of objects. Include as many as you can find (aim for 100+). Be comprehensive."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        text = response.choices[0].message.content
        # Extract JSON from response (may be wrapped in markdown)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        apis = json.loads(text)
        return apis if isinstance(apis, list) else []
    except Exception as e:
        print(f"OpenAI error: {e}")
        return []


def load_existing_index() -> list[dict]:
    """Load existing legal-apis-index.json if present."""
    path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    if path.exists():
        data = json.loads(path.read_text())
        return data.get("apis", data) if isinstance(data, dict) else data
    return []


def merge_apis(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge new APIs into existing, dedupe by slug."""
    by_slug = {a["slug"]: a for a in existing}
    for a in new:
        slug = a.get("slug") or (a.get("name", "").lower().replace(" ", "-").replace(".", ""))
        if slug and slug not in by_slug:
            by_slug[slug] = {**a, "slug": slug}
    return list(by_slug.values())


def write_index(apis: list[dict]) -> None:
    """Write legal-apis-index.json."""
    path = REPO_ROOT / "docs" / "tools" / "legal-apis-index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "source": "https://datarade.ai/search/products/legal-apis",
        "updated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(apis),
        "apis": apis,
    }, indent=2) + "\n")
    print(f"Wrote {len(apis)} APIs to {path}")


def update_mongodb(apis: list[dict]) -> None:
    """Upsert APIs into MongoDB tools collection. Set has_mcp flag where applicable."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from libs.db import get_tools_collection, ensure_indexes
    except ImportError:
        print("MongoDB: libs.db not found. Skipping DB update.")
        return

    coll = get_tools_collection()
    if coll is None:
        print("MONGODB_URI not set. Skipping DB update.")
        return

    ensure_indexes()
    updated = 0
    for api in apis:
        doc = {
            "slug": api.get("slug", ""),
            "name": api.get("name", ""),
            "category": api.get("category", "legal-api"),
            "use_when": api.get("use_when", ""),
            "provider": api.get("provider", ""),
            "url": api.get("url", ""),
            "has_api": api.get("has_api", True),
            "has_mcp": api.get("has_mcp", False),
            "source": "datarade",
            "last_synced": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        if doc["slug"]:
            coll.update_one(
                {"slug": doc["slug"]},
                {"$set": doc},
                upsert=True,
            )
            updated += 1
    print(f"MongoDB: upserted {updated} tools")


def main() -> int:
    print("Discovering legal APIs via OpenAI...")
    new_apis = discover_legal_apis_via_openai()
    if not new_apis:
        print("No APIs discovered. Check OPENAI_API_KEY.")
        return 1

    existing = load_existing_index()
    merged = merge_apis(existing, new_apis)
    write_index(merged)

    if os.environ.get("MONGODB_URI"):
        try:
            update_mongodb(merged)
        except Exception as e:
            print(f"MongoDB update skipped: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
