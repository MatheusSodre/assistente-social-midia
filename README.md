# Assistente Social Media

Plataforma de geração de marketing para Instagram via agentes IA. Briefing curto → caption + hashtags + headline + imagem de fundo, validados por um Brand Agent antes de chegar ao usuário.

Stack: **FastAPI + Supabase + Anthropic Claude (Sonnet 4.6 / Haiku 4.5) + Gemini Flash Image + React 19 + Konva**.

> Ver **[CLAUDE.md](CLAUDE.md)** para arquitetura, decisões e convenções.
> Ver **[deploy/README.md](deploy/README.md)** para deploy em VPS.

---

## Estrutura

```
backend/    FastAPI + agentes + migrations
frontend/   React + Vite + Tailwind
deploy/     PM2 + Nginx
```

---

## Setup local

### Pré-requisitos
- Python 3.10+ (recomendado 3.13 via [uv](https://github.com/astral-sh/uv))
- Node 20+
- Projeto Supabase com credenciais à mão (URL, anon key, service role, DB password)
- API keys: Anthropic + Google (Gemini)

### 1. Backend

```bash
cd backend
uv venv .venv --python 3.13
VIRTUAL_ENV=$(pwd)/.venv uv pip install -e ".[dev]"

cp .env.example .env
# Preencher: ANTHROPIC_API_KEY, GEMINI_API_KEY,
#            SUPABASE_URL/ANON_KEY/SERVICE_ROLE_KEY,
#            SUPABASE_DB_URL_ADMIN (role postgres),
#            MKT_APP_DB_PASSWORD (você inventa)
#            SUPABASE_DB_URL (role mkt_app, monta DEPOIS de rodar migrações)
$EDITOR .env

.venv/bin/python scripts/run_migrations.py
# Após rodar: edite SUPABASE_DB_URL pra usar mkt_app + MKT_APP_DB_PASSWORD

.venv/bin/uvicorn app.main:app --reload --port 3002
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env
# VITE_AUTH_BYPASS=true em dev. VITE_API_URL=http://localhost:3002
$EDITOR .env

npm install
npm run dev   # http://localhost:5173
```

### 3. Testes

```bash
cd backend && .venv/bin/pytest tests/ -v
```

O `test_rls_isolation.py` valida que a RLS isola tenants — se quebrar, todo o modelo de segurança está comprometido.

---

## Smoke

```bash
# 1) Cria Brand Memory
curl -X POST http://localhost:3002/api/v1/brand-memory \
  -H "Content-Type: application/json" \
  -d '{"name":"Minha marca","positioning":"...","tone_of_voice":{"style":"..."}}'

# 2) Gera conteúdo
curl -X POST http://localhost:3002/api/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"brief":"Anúncio do novo serviço X"}'

# 3) Acompanha via SSE
curl -N http://localhost:3002/api/v1/generations/<id>/stream
```

---

## Variáveis de ambiente importantes

Backend (`backend/.env`):

| Var | O que é |
|---|---|
| `ANTHROPIC_API_KEY` | Sonnet 4.6 + Haiku 4.5 |
| `GEMINI_API_KEY` | Gemini Flash Image |
| `SUPABASE_DB_URL` | Conexão asyncpg (role `mkt_app`, **sem BYPASSRLS**) |
| `SUPABASE_DB_URL_ADMIN` | Apenas pro `run_migrations.py` (role `postgres`) |
| `MKT_APP_DB_PASSWORD` | Senha do role `mkt_app` (criada na migração 000a) |
| `AUTH_BYPASS` | `true` em dev, `false` em produção |
| `GEMINI_MODEL_IMAGE` | ID muda com frequência — confira em https://ai.google.dev/gemini-api/docs/models |

---

## Comandos úteis

```bash
# Backend
cd backend
.venv/bin/python scripts/run_migrations.py    # Aplica migrations pendentes (idempotente)
.venv/bin/pytest tests/ -v                     # Testes
.venv/bin/uvicorn app.main:app --reload        # Dev server

# Frontend
cd frontend
npm run dev      # Vite dev server
npm run build    # Build estático em dist/
npm run preview  # Serve dist/ pra teste
```

---

## Licença

Propriedade da Orbitaia. Uso interno.
