-- Applicants table (matches module_5 schema)
CREATE TABLE IF NOT EXISTS applicants (
  p_id SERIAL PRIMARY KEY,
  program TEXT,
  comments TEXT,
  date_added DATE,
  url TEXT,
  status TEXT,
  term TEXT,
  us_or_international TEXT,
  gpa DOUBLE PRECISION,
  gre DOUBLE PRECISION,
  gre_v DOUBLE PRECISION,
  gre_aw DOUBLE PRECISION,
  degree TEXT,
  llm_generated_program TEXT,
  llm_generated_university TEXT
);

-- Unique constraint for idempotency
CREATE UNIQUE INDEX IF NOT EXISTS uq_applicants_url ON applicants(url);

-- Watermarks for incremental ingestion (idempotent scraping)
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
  source TEXT PRIMARY KEY,
  last_seen TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Optional analytics cache that worker writes and web reads
CREATE TABLE IF NOT EXISTS analytics_cache (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);
