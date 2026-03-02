Architecture
============

Web
---
- ``src/flask_app.py`` exposes ``create_app`` and routes.

DB / ETL
--------
- ``src/db.py`` creates the Module 3 ``applicants`` table and unique index on ``url``.
- ``src/etl.py`` inserts rows with ``ON CONFLICT DO NOTHING`` (idempotent pulls).

Analysis
--------
- ``src/query_data.py`` runs the same SQL analysis as Module 3 and formats percentages to 2 decimals.
