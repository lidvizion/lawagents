# AGENTS.md

## Cursor Cloud specific instructions

This is a **documentation-only repository** (Markdown + JSON knowledge base for law firms). There is no frontend, backend, database, or build system.

### Executable component

The only runnable code is `scripts/sync-tools.py` — a Python 3.11+ script using only stdlib (no pip dependencies). It syncs community insights from Reddit/X/Threads into `roles/*/COMMUNITY_INSIGHTS.md` and updates `docs/agent-index.json` and `README.md`.

### Running the sync script

```bash
python3 scripts/sync-tools.py
```

Without API secrets (`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `X_BEARER_TOKEN`, `THREADS_ACCESS_TOKEN`), the script still runs successfully but produces 0 community insight updates — this is expected behavior, not an error.

### Lint / test / build

There are no lint, test, or build commands. The repo has no `package.json`, `requirements.txt`, or any dependency files. Validation is limited to:

- Confirming `docs/agent-index.json` is valid JSON: `python3 -c "import json; json.load(open('docs/agent-index.json'))"`
- Running the sync script without errors: `python3 scripts/sync-tools.py`

### CI

GitHub Actions workflow `.github/workflows/sync-tools.yml` runs the sync script hourly. It uses Python 3.11.
