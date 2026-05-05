CREATE TABLE IF NOT EXISTS mkt_schema_migrations (
  filename   text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
