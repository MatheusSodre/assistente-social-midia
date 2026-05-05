# Deploy — VPS Hostinger

Procedimento pra subir o `assistente-social-media` em produção, usando o
domínio **socialmedia.orbitaia.com.br** e a porta **3002** pro backend.

## Pré-requisitos

- VPS Ubuntu (testado em 22.04 LTS)
- Python 3.13 (recomendado via `uv`) ou 3.10+
- Node 22+ e npm
- Nginx
- PM2 (`npm install -g pm2`)
- Certbot (`sudo apt install certbot python3-certbot-nginx`)
- Acesso ao Supabase (credenciais já configuradas em `.env`)

## 1. Backend

```bash
sudo mkdir -p /opt/assistente-social-media-backend
sudo chown -R $USER:$USER /opt/assistente-social-media-backend
git clone <repo-url> /opt/assistente-social-media-backend
cd /opt/assistente-social-media-backend/backend

# Venv via uv (mais rápido)
uv venv .venv --python 3.13
VIRTUAL_ENV=$(pwd)/.venv uv pip install -e .

# .env de produção
cp .env.example .env
$EDITOR .env
# Importante:
#   AUTH_BYPASS=false
#   FRONTEND_URL=https://socialmedia.orbitaia.com.br
#   SUPABASE_DB_URL apontando pro role mkt_app
#   SUPABASE_DB_URL_ADMIN apontando pro role postgres (só pra rodar migrações)

# Roda migrações no Supabase de produção
.venv/bin/python scripts/run_migrations.py

# Cria diretório de logs e inicia via PM2
sudo mkdir -p /var/log/orbitaia && sudo chown $USER:$USER /var/log/orbitaia
pm2 start ../deploy/ecosystem.config.js
pm2 save
pm2 startup    # configura auto-start no boot (segue instrução do output)
```

## 2. Frontend

```bash
sudo mkdir -p /opt/assistente-social-media-frontend
sudo chown -R $USER:$USER /opt/assistente-social-media-frontend
# se o repo já está clonado em /opt/assistente-social-media-backend, basta apontar:
ln -s /opt/assistente-social-media-backend/frontend /opt/assistente-social-media-frontend

cd /opt/assistente-social-media-frontend
cp .env.example .env
$EDITOR .env
# VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_AUTH_BYPASS=false
# VITE_API_URL=https://socialmedia.orbitaia.com.br

npm install
npm run build
# Build vai pra ./dist — Nginx serve esse diretório
```

## 3. Nginx + HTTPS

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/socialmedia.orbitaia.com.br
# Antes do certbot: comente as linhas SSL e o redirect 301, deixe só o server :80
sudo ln -s /etc/nginx/sites-available/socialmedia.orbitaia.com.br /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Emite certificado e ajusta o conf
sudo certbot --nginx -d socialmedia.orbitaia.com.br

# Restaurar redirect HTTP → HTTPS (descomente o bloco redirect 301)
sudo nginx -t && sudo systemctl reload nginx
```

## 4. Atualizações posteriores

```bash
cd /opt/assistente-social-media-backend
git pull
cd backend
VIRTUAL_ENV=$(pwd)/.venv uv pip install -e .
.venv/bin/python scripts/run_migrations.py
pm2 restart assistente-social-media-backend

cd ../frontend
npm install
npm run build
# Nginx serve o novo dist automaticamente (sem reload)
```

## 5. Logs e troubleshooting

```bash
pm2 logs assistente-social-media-backend            # logs do backend
tail -f /var/log/nginx/error.log                    # erros Nginx
tail -f /var/log/orbitaia/social-media-backend.err.log

# SSE não chega no browser?
# Confirme que nginx.conf NÃO tem proxy_buffering ativo na rota /stream.

# Backend não conecta no DB?
# .venv/bin/python -c "from app.core.dsn import parse_postgres_dsn; import os; from dotenv import load_dotenv; load_dotenv(); print(parse_postgres_dsn(os.environ['SUPABASE_DB_URL']))"
```

## 6. Quando trocar o ID do modelo Gemini

Os IDs `gemini-3.1-flash-image-preview`, `gemini-2.5-flash-image`, etc., mudam
com frequência. Quando precisar trocar:

1. Confirme o ID atual em https://ai.google.dev/gemini-api/docs/models
2. `$EDITOR /opt/assistente-social-media-backend/backend/.env` → atualize `GEMINI_MODEL_IMAGE=...`
3. `pm2 restart assistente-social-media-backend`

Não precisa de redeploy. Pra trocar de Gemini para Imagen/DALL-E (mudança de
provider, não de ID), implemente uma classe que satisfaça o Protocol
`ImageProvider` em `app/integrations/` e troque uma linha do factory em
`app/agents/__init__.py`. O resto do app não muda.
