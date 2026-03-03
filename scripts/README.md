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

## sync-tools.py

Hourly sync: searches **Reddit, X, Threads** for content specific to each role; writes `roles/{role}/COMMUNITY_INSIGHTS.md`; updates `docs/agent-index.json` and `README.md`.

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
