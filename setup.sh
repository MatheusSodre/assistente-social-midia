#!/usr/bin/env bash
# =============================================================================
# setup.sh — Instalação completa do projeto
# Uso: bash setup.sh <nome-do-banco>
# Exemplo: bash setup.sh db_assistente_social
# =============================================================================
set -e

# ---------- parâmetros -------------------------------------------------------
DB_NAME="${1:-db_meu_projeto}"
BACKEND_DIR="apps/backend"
FRONTEND_DIR="apps/frontend"

echo ""
echo "======================================"
echo " Setup do projeto"
echo " Banco: $DB_NAME"
echo "======================================"
echo ""

# ---------- 1. .env backend --------------------------------------------------
if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  sed -i "s/MYSQL_DATABASE=.*/MYSQL_DATABASE=$DB_NAME/" "$BACKEND_DIR/.env"
  echo "✓ $BACKEND_DIR/.env criado (preencha GOOGLE_CLIENT_ID, JWT_SECRET, ANTHROPIC_API_KEY)"
else
  echo "→ $BACKEND_DIR/.env já existe, pulando"
fi

# ---------- 2. .env frontend -------------------------------------------------
if [ ! -f "$FRONTEND_DIR/.env" ]; then
  cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
  echo "✓ $FRONTEND_DIR/.env criado (preencha VITE_GOOGLE_CLIENT_ID)"
else
  echo "→ $FRONTEND_DIR/.env já existe, pulando"
fi

# ---------- 3. banco de dados ------------------------------------------------
echo ""
echo "Criando banco '$DB_NAME' no MySQL..."
read -rsp "Senha do MySQL (usuário root): " MYSQL_PASS
echo ""
mysql -u root -p"$MYSQL_PASS" -e \
  "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "✓ Banco '$DB_NAME' criado"

# atualiza o .env com a senha informada
sed -i "s/MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$MYSQL_PASS/" "$BACKEND_DIR/.env"
sed -i "s/MYSQL_DATABASE=.*/MYSQL_DATABASE=$DB_NAME/" "$BACKEND_DIR/.env"

# ---------- 4. venv + dependências backend -----------------------------------
echo ""
echo "Instalando dependências do backend..."
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi
"$BACKEND_DIR/.venv/bin/pip" install -q --upgrade pip
"$BACKEND_DIR/.venv/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"
echo "✓ Backend pronto"

# ---------- 5. dependências frontend -----------------------------------------
echo ""
echo "Instalando dependências do frontend..."
npm install --prefix "$FRONTEND_DIR" --silent
echo "✓ Frontend pronto"

# ---------- 6. JWT_SECRET automático (se vazio) ------------------------------
JWT_CURRENT=$(grep "^JWT_SECRET=" "$BACKEND_DIR/.env" | cut -d= -f2)
if [ -z "$JWT_CURRENT" ]; then
  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" "$BACKEND_DIR/.env"
  echo "✓ JWT_SECRET gerado automaticamente"
fi

# ---------- resumo final -----------------------------------------------------
echo ""
echo "======================================"
echo " Instalação concluída!"
echo "======================================"
echo ""
echo "Próximos passos obrigatórios:"
echo "  1. Edite $BACKEND_DIR/.env e preencha:"
echo "       GOOGLE_CLIENT_ID=<seu-client-id>.apps.googleusercontent.com"
echo "       ANTHROPIC_API_KEY=sk-ant-..."
echo ""
echo "  2. Edite $FRONTEND_DIR/.env e preencha:"
echo "       VITE_GOOGLE_CLIENT_ID=<seu-client-id>.apps.googleusercontent.com"
echo ""
echo "  3. No Google Cloud Console, adicione às Origens autorizadas:"
echo "       http://localhost:5173"
echo ""
echo "Para rodar o projeto:"
echo "  bash start.sh"
echo ""
