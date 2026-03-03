# Scripts

## crawl-datarade-legal-apis.py

Crawls **dataRade.ai** legal APIs and updates MongoDB. dataRade does not expose a public API (site is behind Cloudflare), so we use OpenAI to discover legal APIs from its knowledge, merge with a curated list, and upsert into the `tools` collection.

### Run

```bash
export MONGODB_URI="mongodb://..."
export OPENAI_API_KEY="sk-..."   # or OPENAI_KEY
pip install -r requirements.txt
python3 scripts/crawl-datarade-legal-apis.py
```

### Output

- Upserts tools into MongoDB `lawagents.tools`
- Writes `docs/tools/legal-apis-index.json` with the discovered APIs

---
Discovers **200+ legal APIs and platforms** via OpenAI. Writes `docs/tools/legal-apis-index.json` and upserts to MongoDB.

```bash
export OPENAI_API_KEY=sk-...   # or OPENAI_KEY
export MONGODB_URI=...         # optional; for DB upsert
pip install -r requirements.txt
python scripts/crawl-datarade-legal-apis.py
```

Source: [dataRade legal APIs](https://datarade.ai/search/products/legal-apis). Includes curated tools (Bloomberg Law Dockets, LegiScan, OpenLaws, TrustFoundry) and static expansion from known legal tech.

## seed-tools.py

Seeds MongoDB from `legal-apis-index.json` and `agent-index.json`. Run after crawl to sync DB.

```bash
export MONGODB_URI=...
python scripts/seed-tools.py
```

## sync-tools.py

Hourly sync: searches **Reddit, X, Threads** for content specific to each role; writes `roles/{role}/COMMUNITY_INSIGHTS.md`; updates `docs/agent-index.json` and `README.md`.

## search-tools.py

Daily search for **new legal tools**: Reddit (legal AI, law firm software, etc.), directories (Law Leaders, Sana Labs, G2). Outputs to `docs/tools/TOOL-DISCOVERIES.md` for manual review.

### Run manually

```bash
# With Reddit (optional; improves Reddit results)
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
python scripts/search-tools.py
```

### Run via cron (server)

```
0 6 * * * cd /path/to/lawagents && python scripts/search-tools.py && git add docs/tools/TOOL-DISCOVERIES.md && git diff --staged --quiet || (git commit -m "chore: tool discoveries" && git push)
```

### Run via GitHub Actions

Workflow runs daily at 06:00 UTC. Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to repo Secrets for Reddit search.

### Role-specific search

For each role (paralegal, marketing-specialist, billing-finance-manager, etc.), the script searches:
- **Reddit:** r/LawFirm, r/Lawyertalk, r/paralegal — role-specific terms
- **X (Twitter):** When `X_BEARER_TOKEN` is set
- **Threads:** When `THREADS_ACCESS_TOKEN` is set

### Run manually

```bash
# With Reddit (create app at https://www.reddit.com/prefs/apps)
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
python scripts/sync-tools.py
```

### Run via cron (server)

```
0 * * * * cd /path/to/lawagents && REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... python scripts/sync-tools.py && git add docs/ agent-index.json README.md roles/*/COMMUNITY_INSIGHTS.md roles/*/README.md && git diff --staged --quiet || (git commit -m "chore: sync" && git push)
```

### Run via GitHub Actions

Workflow runs every hour. Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to repo Secrets for Reddit search. Without them, COMMUNITY_INSIGHTS.md files are created with setup instructions.

---

## crawl-datarade-legal-apis.py

Discovers legal APIs from dataRade and known sources. Writes `docs/tools/legal-apis-index.json` and optionally updates MongoDB.

```bash
# With OPENAI_API_KEY for full crawl (100+ APIs via OpenAI)
export OPENAI_API_KEY=sk-...
python scripts/crawl-datarade-legal-apis.py

# Without: uses static list of 15 APIs
python scripts/crawl-datarade-legal-apis.py
```

With `MONGODB_URI`, upserts tools with `has_api`, `has_mcp` flags.

---

## seed-tools.py

Seeds MongoDB from `docs/agent-index.json` and curated tools (Bloomberg, TrustFoundry, LegiScan, OpenLaws). Sets `has_mcp` for Buffer, Hootsuite, Zapier Clio MCP.

```bash
export MONGODB_URI=mongodb://...
python scripts/seed-tools.py
```
