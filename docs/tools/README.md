# Tool Catalog

Detailed tool inventory with **when to use**, **scoring**, and **sync sources**. Pairs with [Law Firm Tools & Technologies](../law-firm-tools-and-technologies.md).

---

## When to Use: Decision Tree

```
What do you need?
│
├─ Practice management (matters, contacts, billing, calendar)
│  ├─ Solo / small firm (1–10 attorneys)     → Clio, MyCase, Smokeball
│  ├─ PI-specific (contingency)              → CASEpeer, CloudLex, SmartAdvocate
│  └─ Midsize (50+ attorneys)                 → Aderant, Elite, CARET Legal
│
├─ Transaction management (deals, checklists, closing)
│  ├─ Real estate                            → Litera Transact (Real Estate)
│  ├─ Corporate / M&A                        → Litera Transact, CARET Legal
│  └─ IP / trademark                         → LexiDots, Lexair, Alt Legal
│
├─ E-discovery (doc review, production)
│  ├─ Occasional / small matters             → Goldfynch, Logikull
│  ├─ Mid-size matters                       → Everlaw
│  └─ Large / enterprise                     → Relativity
│
├─ Intake / CRM
│  ├─ With Clio                              → Clio Grow
│  └─ Standalone                             → Lawmatics, Clio Grow
│
├─ Legal AI
│  ├─ Law firms (large)                      → Harvey
│  └─ In-house / solo GC                    → GC.AI
│
├─ Social scheduling (marketing)
│  ├─ Multi-channel (8+ platforms)           → Planable
│  ├─ MCP / AI agent control                 → Buffer, Hootsuite
│  └─ Legal-specific                         → Thunderhead, Apaya
│
└─ Integrations / automation
   ├─ No-code                                → Zapier (Clio MCP, etc.)
   └─ API                                    → Clio API, vendor APIs
```

---

## Tool Categories

| Category | Use When | Top Tools | Catalog |
|----------|----------|-----------|---------|
| **Practice management** | Core system for matters, billing, docs | Clio, MyCase, Filevine | [catalog/](catalog/) |
| **Transaction management** | Real estate, corporate closings | Litera Transact | [catalog/](catalog/) |
| **IP / trademark** | Docketing, USPTO deadlines | LexiDots, Alt Legal | [catalog/](catalog/) |
| **E-discovery** | Doc review, production | Everlaw, Goldfynch, Logikull | [catalog/](catalog/) |
| **PI-specific** | Contingency, SOL, liens | CASEpeer, CloudLex, SmartAdvocate | [catalog/](catalog/) |
| **Intake / CRM** | Lead capture, pipeline | Clio Grow, Lawmatics | [catalog/](catalog/) |
| **Legal AI** | Research, contracts, drafting | Harvey, GC.AI | [catalog/](catalog/) |
| **Social scheduling** | Multi-channel; MCP | Planable, Buffer, Hootsuite | [catalog/](catalog/) |
| **Integrations** | Connect tools, automate | Zapier, Clio MCP | [catalog/](catalog/) |

---

## Scoring

Tools are scored 0–10 using:

- **Numeric ratings** (G2, Capterra, SoftwareReviews)
- **Sentiment** (review text, Reddit)
- **Review count** (confidence)
- **Recency** (prefer recent reviews)
- **Feature fit** (practice area match)

See [SCORING-METHODOLOGY.md](SCORING-METHODOLOGY.md). Sync URLs: [SYNC-SOURCES.md](SYNC-SOURCES.md).

---

## Catalog Index

| Tool | Category | Score | When to Use |
|------|----------|-------|-------------|
| [Clio](catalog/clio.md) | Practice management | 9.0 | Solo–mid; general practice; start here |
| [MyCase](catalog/mycase.md) | Practice management | 8.2 | Solo–small; PI, family, immigration |
| [Filevine](catalog/filevine.md) | Practice management | 8.0 | PI, litigation; doc-heavy |
| [CASEpeer](catalog/casepeer.md) | PI-specific | 8.5 | Personal injury; SOL, liens |
| [CloudLex](catalog/cloudlex.md) | PI-specific | 8.5 | Plaintiff PI; integrated suite |
| [Everlaw](catalog/everlaw.md) | E-discovery | 8.8 | Civil litigation; doc review |
| [Litera Transact](catalog/litera-transact.md) | Transaction management | — | Real estate, corporate closings |
| [LexiDots](catalog/lexidots.md) | IP / trademark | — | Trademark docketing, USPTO |
| [Alt Legal](catalog/altlegal.md) | IP / trademark | — | Trademark docketing |
| [Zapier Clio MCP](catalog/zapier-clio-mcp.md) | Integrations | — | AI agent; no-code Clio actions |
| [Harvey](catalog/harvey.md) | Legal AI | — | Large law firms; research, contracts, due diligence |
| [GC.AI](catalog/gc-ai.md) | Legal AI | — | In-house legal; solo GC; contract review, Word |
| [Planable](catalog/planable.md) | Social scheduling | — | Multi-channel; LinkedIn, FB, X, IG, YouTube, etc. |
| [Buffer](catalog/buffer.md) | Social scheduling | — | MCP; simple queue; AI agent control |
| [Hootsuite](catalog/hootsuite.md) | Social scheduling | — | MCP; unified inbox; enterprise |
| [Bloomberg Law Dockets API](catalog/bloomberg-law-dockets-api.md) | Court data | — | Enterprise court docket search |
| [TrustFoundry AI](catalog/trustfoundry-ai.md) | Legal AI | — | Legal research; solo/small firm |
| [LegiScan API](catalog/legiscan.md) | Legislative API | — | Bill data; all 50 states + Congress |
| [OpenLaws API](catalog/openlaws-api.md) | Legislative API | — | Statutes, regulations; RAG/LLM |

*Scores updated from sync sources. `—` = not yet scored.*

*Legal APIs index:* See [legal-apis-index.json](legal-apis-index.json) for dataRade-sourced APIs.

---

## Related

- [Law Firm Tools & Technologies](../law-firm-tools-and-technologies.md) — Clio deep dive, guardrails, branching
- [Practice Areas](../../practice-areas/README.md) — Tools by practice type
- [MAINTENANCE](../../MAINTENANCE.md) — Sync workflow, adding tools
