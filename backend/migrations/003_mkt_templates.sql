DO $do$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mkt_template_type') THEN
    CREATE TYPE mkt_template_type AS ENUM ('post', 'carousel_slide', 'story');
  END IF;
END
$do$;

CREATE TABLE IF NOT EXISTS mkt_templates (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          text NOT NULL,
  type          mkt_template_type NOT NULL,
  dimensions    jsonb NOT NULL,
  slots         jsonb NOT NULL,
  layout_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at    timestamptz NOT NULL DEFAULT now()
);
