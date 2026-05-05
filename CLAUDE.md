# CLAUDE.md — Assistente Social Media (Orbitaia)

Plataforma standalone que gera marketing para Instagram (posts e carrosseis) a partir de um briefing curto, usando agentes de IA orquestrados.

Em modo **dogfood**: usado pela própria Orbitaia. Caminho de evolução: SaaS multi-tenant.

---

## Arquitetura em 1 minuto

```
[ Briefing ] → POST /api/v1/generations
                       │
              ┌────────▼────────┐
              │  Orchestrator   │ Sonnet 4.6 — gera plano de 1-3 frases
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Content Agent │ Sonnet 4.6 — caption, hashtags,
              │                 │              visual_brief, headline
              │     (tool_use)  │ → JSON garantido pelo schema
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Visual Agent  │ Gemini Flash Image — só background.png
              │   (sha256       │ → cache em mkt_assets.metadata
              │    cache)       │ → Storage: mkt-generations/{tenant}/{gen}/
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │   Brand Agent   │ Haiku 4.5 — aprovado / reprovado +
              │     (tool_use)  │             reason + suggestions
              └────────┬────────┘
                       │ (1 retry se reprovado)
                       ▼
              [ result em mkt_generations.result ]
              [ frontend compõe: bg + headline + logo via Konva ]
```

---

## Stack

| Camada | Escolha |
|---|---|
| Backend | FastAPI + Uvicorn, Python 3.13 (≥3.10 OK), asyncpg + LISTEN/NOTIFY, sse-starlette |
| Frontend | React 19 + Vite + TypeScript strict + Tailwind + shadcn-style + Konva |
| DB / Auth / Storage | Supabase (Postgres, Auth, Storage), pgvector preparado pra v2 |
| LLMs | Anthropic Sonnet 4.6 (Orchestrator + Content), Haiku 4.5 (Brand) |
| Imagem | Gemini 3.1 Flash Image / Nano Banana 2 (configurável) |
| Deploy | PM2 :3002 + Nginx em `socialmedia.orbitaia.com.br` |

---

## Estrutura

```
backend/
  app/
    main.py                 # FastAPI lifespan + factory
    api/                    # routers: brand_memory, templates, generations, assets
    services/               # cost_tracker, asset_cache, storage_service,
                            # brand_memory_service, template_service, generation_service
    agents/                 # orchestrator, content_agent, visual_agent, brand_agent
      protocols.py          # CostTracker, AssetCache (interfaces)
      prompts/              # system prompts em .md (iteração sem deploy)
    integrations/           # llm_provider (Protocol) + image_provider (Protocol)
                            # + AnthropicLLMProvider, GeminiImageProvider, SupabaseStorage
    models/                 # Pydantic schemas
    core/                   # config, auth (Supabase JWT + AUTH_BYPASS), db (tenant_context), logging
  migrations/               # 000–009 SQL puro, idempotente
  scripts/run_migrations.py # runner transacional + mkt_schema_migrations
  tests/test_rls_isolation.py

frontend/
  src/
    pages/                  # Login, Dashboard, CreatePost, BrandMemory, History, Templates
    components/
      layout/               # Sidebar, Topbar, Layout
      ui/                   # button, input, textarea, card, label (shadcn-style)
      marketing/            # BriefingForm, GenerationProgress, KonvaComposer,
                            # PreviewCard, ExportButtons, ListEditor
    hooks/                  # useAuth, useGeneration, useSSE, useTemplates, useBrandMemory
    lib/                    # supabase, api-client, utils

deploy/
  ecosystem.config.js
  nginx.conf.example
  README.md
```

---

## Decisões de arquitetura

1. **RLS é rede de segurança real, não defesa em profundidade decorativa.** O backend conecta como role `mkt_app` **sem** `BYPASSRLS`. Toda query passa por `tenant_context(pool, tenant_id)` em `app/core/db.py`, que faz `set_config('request.jwt.claims', $1, true)`. Sem isso, a query FALHA — não silenciosamente vaza.

2. **Tool use, sem JSON parse.** Content e Brand agents usam `tool_use` da Anthropic com `input_schema`. A SDK devolve `tool_use.input` já validado. Zero `json.loads` em string solta, zero retry de parse.

3. **Agentes dependem de Protocols, nunca de clients.** `VisualAgent` depende de `ImageProvider`; trocar Gemini por Imagen/DALL-E é mudança de 1 linha no factory `app/agents/__init__.py`. Mesma coisa pros LLMs.

4. **Cache de imagem por hash semântico.** `sha256(visual_brief + json(visual_identity, sort_keys) + str(template_id))` → lookup em `mkt_assets.metadata->>'cache_hash'` antes de chamar Gemini. Hit = signed URL existente, sem custo de geração.

5. **Migrations versionadas, idempotentes, transacionais.** Tabela `mkt_schema_migrations` registra cada arquivo aplicado. Roda novamente = no-op. Falha = ROLLBACK automático.

6. **SSE via Postgres LISTEN/NOTIFY.** Cada `set_status` no `GenerationService` emite `pg_notify(generation_<id>, payload)`. Endpoint `/generations/:id/stream` faz `LISTEN` e relaya. Sem polling, sem fila adicional.

7. **ZIP de carrossel no backend, não no frontend.** Stdlib `zipfile` em `services/storage_service.py`, salvo em `mkt-exports/{tenant}/{gen}/carousel.zip`, frontend só baixa via signed URL.

8. **Auth bypass via env var.** `AUTH_BYPASS=true` em dev, `false` em produção. Frontend e backend respeitam. Não trava desenvolvimento, não vaza pra produção.

---

## Comandos

```bash
# Setup local
cd backend
uv venv .venv --python 3.13
VIRTUAL_ENV=$(pwd)/.venv uv pip install -e ".[dev]"
cp .env.example .env && $EDITOR .env
.venv/bin/python scripts/run_migrations.py
.venv/bin/uvicorn app.main:app --reload --port 3002

cd ../frontend
cp .env.example .env && $EDITOR .env
npm install
npm run dev   # :5173

# Tests
cd backend && .venv/bin/pytest tests/ -v

# Smoke API
curl http://127.0.0.1:3002/health
curl -X POST http://127.0.0.1:3002/api/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"brief": "..."}'
```

---

## Convenções de código

### Python
- Type hints em tudo. `from __future__ import annotations` quando precisar de forward refs.
- Pydantic 2 pra schemas. `model_dump_json()` pra serializar pra DB.
- Async via asyncpg direto, sem ORM. Toda query dentro de `tenant_context`.
- Logs estruturados em JSON via `core/logging.py`.

### TypeScript
- Strict mode. Aliases via `@/*`.
- Componentes UI no padrão shadcn (cva + forwardRef + cn helper).
- Estado simples via useState. Sem zustand/redux no MVP.
- API calls via wrapper `lib/api-client.ts` (que injeta Authorization automaticamente).

### Banco
- Toda tabela nova tem prefixo `mkt_*`.
- RLS habilitada e policies escritas com `mkt_current_tenant()`.
- Triggers de `updated_at` reusam `mkt_set_updated_at()`.

---

## Roadmap pós-MVP

- [ ] Performance Agent: post-publicação, lê métricas do IG e ajusta tom
- [ ] Research Agent: scrape de concorrentes pra popular `competitors`
- [ ] RAG sobre `examples` via pgvector (já habilitado)
- [ ] Publicação direta no Instagram via Meta Graph API
- [ ] Multi-template carrossel (gera N slides em batch)
- [ ] Webhook pra Slack/WhatsApp quando geração fica pronta

---

## Tarefas que NÃO entram aqui

- **Não criar tabelas sem prefixo `mkt_*`** — colide com outros projetos no mesmo Supabase.
- **Não bypass RLS no backend** — sempre `mkt_app` + `tenant_context`. `service_role` é só para Storage/Auth admin via SDK.
- **Não imprima senhas/JWTs em logs.**
- **Não publique conteúdo sem aprovação humana** — o `brand_review.approved` do Brand Agent é uma sugestão, não autorização final. UX exige clique do usuário.
