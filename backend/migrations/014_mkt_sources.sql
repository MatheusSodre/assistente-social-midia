DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_source_type') THEN
    CREATE TYPE mkt_source_type AS ENUM (
      'website', 'instagram', 'linkedin', 'pdf', 'chat'
    );
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_source_status') THEN
    CREATE TYPE mkt_source_status AS ENUM (
      'pending', 'processing', 'indexed', 'error'
    );
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_sources (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         uuid NOT NULL,
  type              mkt_source_type NOT NULL,
  name              text NOT NULL,
  url_or_path       text NOT NULL,
  status            mkt_source_status NOT NULL DEFAULT 'pending',
  items_count       int,
  error_message     text,
  metadata          jsonb NOT NULL DEFAULT '{}'::jsonb,  -- conteúdo extraído, summary, etc.
  added_by_user_id  uuid,
  added_via_chat    bool NOT NULL DEFAULT false,
  last_indexed_at   timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_sources_tenant_idx ON mkt_sources(tenant_id);
CREATE INDEX IF NOT EXISTS mkt_sources_status_idx ON mkt_sources(status)
  WHERE status IN ('pending', 'processing');

DROP TRIGGER IF EXISTS mkt_sources_updated_at ON mkt_sources;
CREATE TRIGGER mkt_sources_updated_at
  BEFORE UPDATE ON mkt_sources
  FOR EACH ROW EXECUTE FUNCTION mkt_set_updated_at();
