CREATE TABLE IF NOT EXISTS mkt_agent_logs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  generation_id uuid NOT NULL REFERENCES mkt_generations(id) ON DELETE CASCADE,
  agent_name    text NOT NULL,
  model         text NOT NULL,
  input         jsonb NOT NULL,
  output        jsonb NOT NULL,
  tokens_in     int NOT NULL DEFAULT 0,
  tokens_out    int NOT NULL DEFAULT 0,
  cost_cents    int NOT NULL DEFAULT 0,
  latency_ms    int NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mkt_agent_logs_generation_idx
  ON mkt_agent_logs(generation_id);
