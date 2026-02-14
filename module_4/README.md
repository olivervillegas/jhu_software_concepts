# Module 4 — Grad Café Analytics (Pytest + Sphinx)

This refactor matches your Module 3 schema and satisfies the Module 4 rubric:

- Flask **create_app(...)** factory
- **GET /analysis** renders required UI components + selectors
- **POST /pull-data** returns JSON and loads data via injected scraper (tests inject fake)
- **POST /update-analysis** returns JSON and caches results
- Busy gating returns **409 {"busy": true}**
- DB uses **DATABASE_URL** (no hardcoded credentials)
- Idempotency via **UNIQUE(url)** + **ON CONFLICT DO NOTHING**

## Run app
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
python -m src
```

## Run tests
```bash
pytest -m "web or buttons or analysis or db or integration"
```
