CREATE TABLE IF NOT EXISTS mkt_lia_conversations (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          uuid NOT NULL,
  started_by_user_id uuid NOT NULL,
  title              text,                -- auto-gerado depois de N turnos via Haiku
  summary            text,                -- gerado ao fechar conversa pra contexto futuro
  message_count      int NOT NULL DEFAULT 0,
  total_cost_cents   int NOT NULL DEFAULT 0,
  last_message_at    timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now(),
  closed_at          timestamptz
);

CREATE INDEX IF NOT EXISTS mkt_lia_conversations_tenant_idx
  ON mkt_lia_conversations(tenant_id, last_message_at DESC);
