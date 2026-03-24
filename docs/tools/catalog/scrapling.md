# Scrapling

**Category:** Web scraping  
**Use when:** Legal research, due diligence, or automation requires extracting data from public websites (court dockets, corporate filings, competitor sites).

---

## Overview

| Field | Value |
|-------|-------|
| **Product** | [Scrapling](https://github.com/D4Vinci/Scrapling) |
| **Best for** | Adaptive web scraping; anti-bot bypass; legal research automation |
| **Pricing** | Open source (BSD 3-Clause) |
| **Language** | Python (>=3.10) |
| **API** | Python library, CLI, MCP server |

---

## When to Use

| Scenario | Use Scrapling |
|----------|---------------|
| Scrape public court dockets, PACER alternatives | ✅ Yes |
| Corporate filings, SEC EDGAR, state registries | ✅ Yes |
| Competitor or market research from public sites | ✅ Yes |
| Sites with anti-bot (Cloudflare Turnstile, etc.) | ✅ Yes |
| Adaptive parsing when sites change layout | ✅ Yes |
| MCP integration for AI agents | ✅ Yes |
| Large-scale crawls with concurrency limits | ✅ Yes |
| Need real-time sync with practice management | ⚠️ Use Zapier + vendor APIs |

---

## Key Features

- **Adaptive parsing** — Parser learns from website changes and relocates elements when pages update
- **Anti-bot bypass** — Built-in fetchers bypass Cloudflare Turnstile and similar systems
- **Multiple fetchers** — Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
- **Spider framework** — Scrapy-like API for concurrent crawls; per-domain throttling; proxy rotation
- **Pause/resume** — Resume interrupted crawls
- **CLI & MCP** — Command-line and Model Context Protocol server for AI agents

---

## Sync Sources

| Type | URL |
|------|-----|
| GitHub | https://github.com/D4Vinci/Scrapling |
| PyPI | https://pypi.org/project/scrapling/ |
| Docs | https://scrapling.readthedocs.io |

---

## Guardrails

| Action | Approval Level |
|--------|----------------|
| Scrape public records for research | Log only |
| Bulk scrape; store in matter system | Medium |
| Scrape sites with ToS restrictions | Mandatory approval |

---

## Related

- [Zapier Clio MCP](zapier-clio-mcp.md) — Integrations; no-code automation
- [Everlaw](everlaw.md) — E-discovery; doc review
- [IT LegalTech Specialist](../../../roles/it-legaltech-specialist/README.md) — Tool adoption
