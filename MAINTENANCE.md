# Lawagents Maintenance Guide

High-level guide for maintaining and syncing the lawagents toolkit. For small to mid-sized law firms ($2M–$50M annual revenue).

---

## Repository Structure

```
lawagents/
├── examples/                 ← Operations staff workflow examples (COO, billing, intake, paralegal, receptionist, etc.)
├── AGENT_INSTRUCTIONS.md    ← Canonical instructions for AI agents (Claude, ChatGPT, Gemini, Cursor)
├── .cursorrules             ← Cursor: reference this repo for legal tools/roles
├── MAINTENANCE.md            ← You are here. Root maintenance guide.
├── README.md                ← Project overview and doc index
├── docs/
│   ├── law-firm-roles-and-skills.md
│   ├── law-firm-tools-and-technologies.md   ← Tools overview; links to catalog
│   ├── agent-index.json     ← Machine-readable index for AI agents (tools, roles, practice areas)
│   ├── ai-sitemap.md        ← Full sitemap with canonical URLs for agents
│   └── tools/
│       ├── README.md        ← Tool catalog index, when-to-use decision tree
│       ├── SCORING-METHODOLOGY.md
│       ├── SYNC-SOURCES.md  ← URLs to sync for latest ratings, reviews, pricing
│       └── catalog/         ← Individual tool files (one per tool)
│           ├── README.md
│           └── *.md (clio, filevine, casepeer, etc.)
├── roles/                   ← One folder per firm role (25+ roles)
├── practice-areas/          ← Transactional + litigation by practice type
│   ├── transactional/       ← Real estate, corporate, IP, employment, family, estate, immigration, tax
│   └── litigation/         ← PI, criminal, civil
└── practice-areas/RESEARCH-SOURCES.md
```

---

## What to Maintain

| Area | Location | Sync Frequency | Notes |
|------|----------|----------------|-------|
| **Tool ratings & reviews** | `docs/tools/SYNC-SOURCES.md` → catalog | Quarterly | G2, Capterra, SoftwareReviews URLs |
| **Tool pricing** | `docs/tools/catalog/*.md` | Quarterly | Pricing pages, feature changes |
| **API/docs** | `docs/tools/catalog/*.md` | As needed | Developer docs, changelogs |
| **Practice area pain points** | `practice-areas/**/README.md` | Semi-annual | Reddit, industry sources |
| **Role instructions** | `roles/**/README.md` | Annual | Role changes, new workflows |
| **Research sources** | `practice-areas/RESEARCH-SOURCES.md` | Semi-annual | New subreddits, publications |

---

## Sync Workflow

### Automated (hourly)

- **GitHub Actions:** `.github/workflows/sync-tools.yml` runs every hour. Searches Reddit, X, Threads per role; writes `roles/{role}/COMMUNITY_INSIGHTS.md`; updates `docs/agent-index.json` and `README.md`.
- **Secrets (optional):** Add to repo Settings → Secrets for full sync:
  - `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` — [Reddit API apps](https://www.reddit.com/prefs/apps) (create "script" app)
  - `X_BEARER_TOKEN` — X API v2 (optional)
  - `THREADS_ACCESS_TOKEN` — Meta Threads API (optional)
- **Manual/cron:** Run `python scripts/sync-tools.py`. Set env vars for Reddit/X/Threads. See [scripts/README.md](scripts/README.md).

### Manual (quarterly)

1. **Review SYNC-SOURCES.md** — All URLs for ratings, reviews, pricing, API docs.
2. **Visit each source** — G2, Capterra, SoftwareReviews, vendor sites.
3. **Update catalog files** — Refresh scores, sentiment summary, pricing.
4. **Re-run scoring** — Apply methodology in SCORING-METHODOLOGY.md.
5. **Update README** — If tool rankings or recommendations change.

---

## Scoring Methodology

Tool scores combine:

- **Numeric ratings** (G2, Capterra, etc.) — Normalized to 0–10.
- **Sentiment** — Positive/neutral/negative from review text.
- **Review count** — More reviews = higher confidence.
- **Recency** — Prefer recent reviews.

See [docs/tools/SCORING-METHODOLOGY.md](docs/tools/SCORING-METHODOLOGY.md) for full details.

---

## Adding a New Tool

1. Create `docs/tools/catalog/{tool-slug}.md` using existing catalog format.
2. Add sync URLs to `docs/tools/SYNC-SOURCES.md`.
3. Add tool to appropriate category in `docs/tools/README.md`.
4. Update `docs/law-firm-tools-and-technologies.md` if it's a primary integration.

---

## Adding a New Role or Practice Area

1. **Role:** Create `roles/{role-slug}/README.md`; add to `roles/README.md`.
2. **Practice area:** Create `practice-areas/{type}/{area}/README.md`; add to index.
3. **Research:** Add sources to `practice-areas/RESEARCH-SOURCES.md` if applicable.

---

## Database Migration (Future)

When adding a database:

- **Tools catalog** → `tools` table (name, category, score, sync_urls, etc.)
- **Sync sources** → `sync_sources` table (url, type, last_synced)
- **Scores** → `tool_scores` table (tool_id, source, score, sentiment, date)
- **Roles/practice areas** → Can remain markdown or migrate to CMS

Catalog markdown is structured for easy parsing (YAML frontmatter or consistent headings).
