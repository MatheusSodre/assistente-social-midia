# CLAUDE.md

Instruções para Claude Code neste projeto.

## Stack

- **Backend:** Python + FastAPI + PyMySQL (raw SQL) + MySQL 8
- **Frontend:** React 19 + TypeScript 5 + Vite 7 + AdminLTE 3
- **Auth:** Google OAuth + JWT (python-jose)
- **LLM:** Anthropic SDK (Haiku para JSON/classificação, Sonnet para geração)
- **WhatsApp:** Evolution API v1.8.7 (Docker)

## Convenções

- IDs: `CHAR(36)` com `DEFAULT (UUID())` — nunca `AUTO_INCREMENT`
- Toda query de dado de usuário DEVE filtrar por `usuario_id = user["sub"]`
- Soft delete: coluna `ativo TINYINT(1) DEFAULT 1`
- Timestamps: `DATETIME DEFAULT CURRENT_TIMESTAMP`
- TypeScript: `verbatimModuleSyntax` ativo — usar `import type` para types
- Datas para o usuário: formato `dd/mm/AAAA` (Brasil)

## Estrutura

- `apps/backend/api/` — routers FastAPI (camada HTTP)
- `apps/backend/src/` — lógica de negócio (sem HTTP)
- `apps/backend/skills/` — pipelines LLM autônomos
- `apps/frontend/src/` — SPA React

## Banco de dados

- Nunca usar `DROP TABLE` — migrações são aditivas
- `init_db()` roda no startup da aplicação
- DDL fica em `src/db/schema.py` (variável `SCHEMA`)

## Modelos LLM

- Haiku (`claude-haiku-4-5-20251001`): classificação, JSON, temp 0.1
- Sonnet (`claude-sonnet-4-6`): geração de texto, temp 0.2

## Não commitar

- `.env`, arquivos em `storage/`, `logs/`, `tmp/`
