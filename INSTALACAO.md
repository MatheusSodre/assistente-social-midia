# Guia de Instalação

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- MySQL 8 rodando localmente
- Conta Google Cloud com OAuth 2.0 configurado

---

## 1ª vez — Setup completo

```bash
bash setup.sh db_nome_do_projeto
```

O script faz automaticamente:
- Cria `apps/backend/.env` e `apps/frontend/.env` a partir dos `.env.example`
- Cria o banco de dados no MySQL
- Cria o `.venv` Python e instala dependências do backend
- Instala dependências do frontend (`npm install`)
- Gera `JWT_SECRET` automaticamente

### Após o setup, preencher as chaves:

**`apps/backend/.env`**
```
GOOGLE_CLIENT_ID=<client-id>.apps.googleusercontent.com
ANTHROPIC_API_KEY=sk-ant-...
```

**`apps/frontend/.env`**
```
VITE_GOOGLE_CLIENT_ID=<client-id>.apps.googleusercontent.com
```

### Google Cloud Console

No [Google Cloud Console](https://console.cloud.google.com) → Credentials → editar o Client ID → **Origens JavaScript autorizadas**:
```
http://localhost:5173
```

---

## Rodar o projeto

```bash
bash start.sh
```

- Backend: http://localhost:8000
- Docs API: http://localhost:8000/docs
- Frontend: http://localhost:5173

Logs em `/tmp/backend.log` e `/tmp/frontend.log`.

---

## Parar o projeto

```bash
bash stop.sh
```

---

## Banco de dados

O banco é criado pelo `setup.sh`. As tabelas são criadas automaticamente pelo `init_db()` no startup do backend (`src/db/schema.py`).

Para adicionar novas tabelas: edite `apps/backend/src/db/schema.py` — nunca usar `DROP TABLE`.

---

## Estrutura dos scripts

| Script | O que faz |
|--------|-----------|
| `setup.sh <db>` | Instalação completa (rodar 1x por projeto) |
| `start.sh` | Sobe backend + frontend |
| `stop.sh` | Para backend + frontend |
