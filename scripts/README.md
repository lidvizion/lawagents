# Scripts

## sync-tools.py

Hourly sync: checks sync sources (G2, Harvey, GC.AI), updates `docs/agent-index.json` and `README.md` with last synced timestamp.

### Run manually

```bash
python scripts/sync-tools.py
```

### Run via cron (server)

Add to crontab (`crontab -e`):

```
0 * * * * cd /path/to/lawagents && python scripts/sync-tools.py && git add docs/agent-index.json README.md && git diff --staged --quiet || (git commit -m "chore: sync tools" && git push)
```

### Run via GitHub Actions

The workflow `.github/workflows/sync-tools.yml` runs every hour. No setup required for public repos. For manual trigger: Actions → Sync Tools (Hourly) → Run workflow.
