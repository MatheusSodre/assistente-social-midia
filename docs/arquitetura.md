# Arquitetura

## Visão Geral

```
[Browser] → React SPA (AdminLTE)
              ↓ HTTP REST (JWT)
           FastAPI (Uvicorn :8000)
              ↓ PyMySQL (raw SQL)
           MySQL 8
              ↓ Anthropic SDK
           Claude API (LLM)
              ↓ HTTP
           Evolution API (WhatsApp :8080)
```

## Camadas do Backend

| Camada | Pasta | Responsabilidade |
|--------|-------|------------------|
| HTTP | `api/` | Routers, schemas Pydantic, validação |
| Negócio | `src/` | Regras, queries SQL, jobs |
| Skills | `skills/` | Pipelines LLM autônomos |
