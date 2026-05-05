-- Role do backend: SEM BYPASSRLS (RLS aplica a TODA query do backend).
-- service_role da Supabase (que tem BYPASSRLS) fica reservado pra Storage/Auth via SDK.
-- O placeholder <<MKT_APP_PASSWORD>> é substituído pelo run_migrations.py
-- pelo valor de MKT_APP_DB_PASSWORD do .env, com escaping de aspas simples.

DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mkt_app') THEN
    CREATE ROLE mkt_app LOGIN PASSWORD '<<MKT_APP_PASSWORD>>' NOBYPASSRLS;
  ELSE
    ALTER ROLE mkt_app WITH LOGIN PASSWORD '<<MKT_APP_PASSWORD>>' NOBYPASSRLS;
  END IF;
END
$do$;

GRANT USAGE ON SCHEMA public TO mkt_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mkt_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mkt_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mkt_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO mkt_app;
