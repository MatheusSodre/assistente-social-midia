INSERT INTO storage.buckets (id, name, public) VALUES
  ('mkt-brand-assets', 'mkt-brand-assets', false),
  ('mkt-generations',  'mkt-generations',  false),
  ('mkt-exports',      'mkt-exports',      false)
ON CONFLICT (id) DO NOTHING;
