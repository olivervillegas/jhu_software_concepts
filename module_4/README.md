# Module 4 — Grad Café Analytics Service

This module implements a test-driven Flask analytics service built on top of PostgreSQL.

It includes:

- A Flask web application
- Pull Data and Update Analysis endpoints
- Busy-state gating
- Idempotent database inserts
- Formatted analysis output (percentages with two decimals)
- Full pytest test suite (100% coverage enforced)
- GitHub Actions CI
- Sphinx documentation published on Read the Docs

---

## Project Structure

module_4/
│
├── src/ # Application code
│ ├── flask_app.py
│ ├── db.py
│ ├── etl.py
│ ├── query_data.py
│ └── ...
│
├── tests/ # Pytest test suite
├── templates/ # Jinja templates
├── docs/ # Sphinx documentation
├── pytest.ini
├── requirements.txt
├── coverage_summary.txt
├── actions_success.png
└── README.md

---

## Requirements

- Python 3.12+
- PostgreSQL running locally

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variable

Set your database connection:

```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5433/postgres"
```

(Adjust credentials/port as needed.)

## Run the Application

From the module_4/ directory:
```bash
export FLASK_APP=src.flask_app
flask run
```

Then open:
```bash
http://127.0.0.1:5000/analysis
```

## Run Tests

Run all required markers:

```bash
pytest -m "web or buttons or analysis or db or integration"
```

Coverage is enforced at 100% for all code inside src/.

## Continuous Integration

GitHub Actions runs:

- PostgreSQL service container

- Pytest with coverage

- Fails if coverage < 100%

Proof of successful run:
```bash
module_4/actions_success.png
```

## Documentation

Sphinx documentation is located in docs/.

Build locally:
```bash
cd docs
make html
```

Read the Docs site:

https://jhu-software-concepts-module-4.readthedocs.io/en/latest/index.html

Documentation includes:

- Architecture overview

- Application flow

- API routes

- Database schema

- Testing strategy