# Module 5 — Hardened Flask + PostgreSQL Grad Café Analytics

This module hardens a Flask + PostgreSQL analytics app using software assurance workflows:

- Static analysis (Pylint 10/10)
- SQL injection defenses (psycopg SQL composition + parameter binding)
- Enforced LIMIT on every query (plus maximum limit clamping)
- Dependency graph generation (pydeps + Graphviz)
- Reproducible environments (pip+venv and uv)
- Packaging (setup.py + editable installs)
- Supply-chain scanning (Snyk)
- CI enforcement via GitHub Actions

---

## Project Layout

Key directories and files:

- `src/` — application code (ONLY this is linted)
  - `flask_app.py` — Flask app factory + routes
  - `db.py` — DB connection + schema setup (safe SQL composition)
  - `etl.py` — file-based scraper + safe inserts
  - `query_data.py` — safe analytics queries (LIMIT enforced everywhere)
  - `templates/analysis.html` — analysis page
- `tests/` — tests (not linted per instructor requirement)
- `requirements.txt` — runtime + tools (pylint, pydeps)
- `setup.py` — installable package definition
- `.env.example` — example env vars (no secrets)
- `.github/workflows/ci.yml` — CI pipeline

---

## Requirements

### System requirements
- Python 3.11+ recommended
- PostgreSQL 14+ (local or Docker)
- Graphviz installed so the `dot` command is available (required for dependency graph)

### Python dependencies
Installed from `requirements.txt` (includes runtime + tooling).

---

## Environment Variables

This project uses environment variables for DB credentials (no hard-coded secrets):

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

An example is provided in `.env.example`. Copy it to `.env` locally:

```bash
cp .env.example .env
