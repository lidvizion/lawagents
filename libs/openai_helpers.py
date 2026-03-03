"""
OpenAI helpers for tool discovery, sentiment scoring, and semantic search.
"""
import json
import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_client() -> "OpenAI | None":
    """Return OpenAI client. Uses OPENAI_API_KEY or OPENAI_KEY."""
    if OpenAI is None:
        return None
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def discover_legal_tools_batch(
    category: str,
    count: int = 50,
    model: str = "gpt-4o-mini",
) -> list[dict[str, Any]]:
    """
    Use OpenAI to generate a batch of legal tools/APIs for a given category.
    Returns list of {name, slug, category, use_when, url, has_api, has_mcp, provider}.
    """
    client = get_client()
    if not client:
        return []

    prompt = f"""List {count} legal technology tools, APIs, or platforms in the category: {category}.

For each tool, provide:
- name: Full product name
- slug: lowercase hyphenated identifier (e.g. unicourt-api)
- category: one of practice-management, pi-specific, e-discovery, court-data, legislative, ip-trademark, legal-ai, transaction-management, integrations, social-scheduling, document-management, billing, intake-crm, research
- use_when: One sentence when to use (e.g. "Federal court records, PACER data")
- url: Main product or API URL if known
- has_api: true/false
- has_mcp: true/false (Model Context Protocol for AI agents)
- provider: Company/vendor name

Include real products from: dataRade legal APIs, CourtListener, UniCourt, Bloomberg Law, LegiScan, OpenLaws, vLex, Fastcase, Casetext, Westlaw, Lexis, Clio, MyCase, Filevine, CASEpeer, Everlaw, Relativity, Harvey, etc. Also include lesser-known APIs and integrations.

Return ONLY a valid JSON array, no other text. Example:
[{{"name":"UniCourt API","slug":"unicourt-api","category":"court-data","use_when":"Federal and state court records","url":"https://unicourt.com","has_api":true,"has_mcp":false,"provider":"UniCourt"}}]"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Extract JSON from markdown code block if present
        if "```" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def discover_legal_tools_full(target_count: int = 220) -> list[dict[str, Any]]:
    """
    Discover 200+ legal tools across all categories using multiple batches.
    Uses 4 batches of ~60 each to minimize API calls while reaching target.
    """
    categories = [
        (
            "Court data, docket APIs, PACER, state/federal courts. List 70 tools. "
            "Include: UniCourt, CourtListener, Bloomberg Law, LegiScan, OpenLaws, "
            "PACER, RECAP, Trellis, Docket Alarm, Court API, UniCourt API, "
            "APISCRAPY, Grepsr, Xverum, InQuartik, Oxylabs, dataRade legal APIs.",
            70,
        ),
        (
            "Practice management, case management, PI, billing, intake, CRM. List 70 tools. "
            "Include: Clio, MyCase, Filevine, CASEpeer, CloudLex, Smokeball, "
            "PracticePanther, CosmoLex, CARET, Aderant, Elite, Lawmatics, Clio Grow, "
            "Filevine, SmartAdvocate, Needles, TrialWorks, AbacusLaw.",
            70,
        ),
        (
            "E-discovery, document review, legal AI, research platforms. List 70 tools. "
            "Include: Everlaw, Relativity, Goldfynch, Logikull, Harvey, Casetext, "
            "vLex, Fastcase, Westlaw, Lexis, Luminance, Kira, TrustFoundry, "
            "GC.AI, Ross, ROSS Intelligence, Lexis+ AI, Westlaw Edge.",
            70,
        ),
        (
            "Integrations, Zapier, MCP, transaction management, IP/trademark, "
            "marketing, document management. List 70 tools. Include: Zapier Clio MCP, "
            "Litera Transact, LexiDots, Alt Legal, Planable, Buffer, Hootsuite, "
            "DocuSign, InfoTrack, Thunderhead, Apaya, LawRato, Legal.io.",
            70,
        ),
        (
            "Legal data providers, dataRade APIs, company data, compliance data. "
            "List 70 tools. Include: Success.ai, CompanyData/BoldData, Rightsify, "
            "Nubela, Trademo, The Warren Group, Veridion, Forager.ai, Techsalerator, "
            "RapidAPI legal, APILayer, ScrapingBee, legal datasets, court records vendors.",
            70,
        ),
    ]

    seen_slugs: set[str] = set()
    all_tools: list[dict[str, Any]] = []

    for cat_label, count in categories:
        batch = discover_legal_tools_batch(cat_label, count=count)
        for t in batch:
            slug = (t.get("slug") or "").strip().lower().replace(" ", "-")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            t["slug"] = slug
            if "category" not in t or not t["category"]:
                t["category"] = "legal-tech"
            all_tools.append(t)

        if len(all_tools) >= target_count:
            break

    return all_tools[:target_count]
