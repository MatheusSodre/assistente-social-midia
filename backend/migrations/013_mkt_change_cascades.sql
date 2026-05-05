CREATE TABLE IF NOT EXISTS mkt_change_cascades (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  trigger_block_key   mkt_brand_block_key NOT NULL,
  suggested_block_key mkt_brand_block_key NOT NULL,
  trigger_condition   text,  -- descrição humana, validação no service layer
  suggestion_template text NOT NULL,
  enabled             bool NOT NULL DEFAULT true,
  created_at          timestamptz NOT NULL DEFAULT now()
);

-- Seeds iniciais
INSERT INTO mkt_change_cascades (trigger_block_key, suggested_block_key, trigger_condition, suggestion_template) VALUES
  ('icp', 'tone', 'persona muda', 'voz precisa ser ajustada pra novo perfil de audiência'),
  ('icp', 'topics', 'persona muda', 'pilares de conteúdo podem precisar de ajuste'),
  ('tone', 'examples', 'estilo muda', 'exemplos antigos podem não bater com nova voz'),
  ('brand', 'tone', 'posicionamento muda', 'voz pode precisar refletir novo posicionamento'),
  ('brand', 'topics', 'posicionamento muda', 'pilares podem precisar de ajuste')
ON CONFLICT DO NOTHING;
