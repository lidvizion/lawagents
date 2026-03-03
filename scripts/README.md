# Scripts

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
