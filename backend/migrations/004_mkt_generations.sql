DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_generation_status') THEN
    CREATE TYPE mkt_generation_status AS ENUM (
      'pending', 'brand_loading', 'content_generating',
      'image_generating', 'validating', 'done', 'failed'
    );
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_generations (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    uuid NOT NULL,
  brief        text NOT NULL,
  template_id  uuid REFERENCES mkt_templates(id) ON DELETE SET NULL,
  status       mkt_generation_status NOT NULL DEFAULT 'pending',
  result       jsonb NOT NULL DEFAULT '{}'::jsonb,
  cost_cents   int NOT NULL DEFAULT 0,
  created_by   uuid NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS mkt_generations_tenant_idx
  ON mkt_generations(tenant_id);
CREATE INDEX IF NOT EXISTS mkt_generations_status_idx
  ON mkt_generations(status);
CREATE INDEX IF NOT EXISTS mkt_generations_created_at_idx
  ON mkt_generations(created_at DESC);
