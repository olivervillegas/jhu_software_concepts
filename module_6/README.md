# Module 6 — Microservices GradCafe Analytics (Flask + Worker + Postgres + RabbitMQ)

This project refactors the GradCafe analytics app into a microservice stack:

- **web**: Flask UI (publishes tasks to RabbitMQ; does not perform long-running writes in the request)
- **worker**: RabbitMQ consumer (processes tasks; performs DB writes; idempotent; acks after commit)
- **db**: PostgreSQL 16
- **rabbitmq**: RabbitMQ 3.13 (with management UI)

---

## Services and Ports

- Web UI: http://localhost:8080
- RabbitMQ Management UI: http://localhost:15672  
  - username: `guest`  
  - password: `guest`

Postgres is internal to the Docker network by default.

---

## Quickstart

### 1) Create your `.env`

Copy the example env file:

~~~bash
cp .env.example .env
~~~

### 2) Build and run

Start the full stack:

~~~bash
docker compose up --build
~~~

### 3) Use the app

Open:

- http://localhost:8080

Buttons:

- **Pull Data**: enqueues `scrape_new_data`
- **Update Analysis**: enqueues `recompute_analytics`

These endpoints return immediately (HTTP 202 on success). The worker processes tasks asynchronously.

---

## Verifying RabbitMQ

Open the management UI:

- http://localhost:15672

Log in with `guest/guest`. You should see the durable queue `tasks_q`.

---

## Data + Idempotency

- Schema is created by `src/db/init.sql` on first DB init.
- The worker ingests from `src/data/applicant_data.json` (mounted read-only).
- Inserts are idempotent via:
  - a unique index on `applicants(url)`
  - `ON CONFLICT (url) DO NOTHING`
- Incremental ingestion is tracked using:

~~~sql
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
  source TEXT PRIMARY KEY,
  last_seen TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);
~~~

The worker reads `last_seen` and only inserts records newer than the watermark, then advances it after a successful commit.

---

## Docker Images (Registry Links)

Fill these in after you push your images:

- Docker Hub (web): https://hub.docker.com/r/joliverv1/module_6-web
- Docker Hub (worker): https://hub.docker.com/r/joliverv1/module_6-worker

Or, if you used a single repo with tags:

- Docker Hub (repo): https://hub.docker.com/r/joliverv1/module_6  
  - tags: `web-v1`, `worker-v1`

---

## Build + Push Images (examples)

### Option A: Two separate repos (module_6-web and module_6-worker)

~~~bash
docker build -t <YOUR_DOCKERHUB_USER>/module_6-web:v1 ./src/web
docker build -t <YOUR_DOCKERHUB_USER>/module_6-worker:v1 ./src/worker

docker login
docker push <YOUR_DOCKERHUB_USER>/module_6-web:v1
docker push <YOUR_DOCKERHUB_USER>/module_6-worker:v1
~~~

### Option B: One repo (module_6) with tags

~~~bash
docker build -t <YOUR_DOCKERHUB_USER>/module_6:web-v1 ./src/web
docker build -t <YOUR_DOCKERHUB_USER>/module_6:worker-v1 ./src/worker

docker login
docker push <YOUR_DOCKERHUB_USER>/module_6:web-v1
docker push <YOUR_DOCKERHUB_USER>/module_6:worker-v1
~~~

---

## Resetting the Stack (clean DB)

This stops containers and deletes the Postgres volume:

~~~bash
docker compose down -v
~~~

Then rebuild/run again:

~~~bash
docker compose up --build
~~~