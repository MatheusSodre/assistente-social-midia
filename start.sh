#!/usr/bin/env bash
# =============================================================================
# start.sh — Inicia backend e frontend em terminais separados
# Uso: bash start.sh
# =============================================================================
set -e

BACKEND_DIR="apps/backend"
FRONTEND_DIR="apps/frontend"

# verifica pré-requisitos
if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "✗ $BACKEND_DIR/.env não encontrado. Rode: bash setup.sh <nome-do-banco>"
  exit 1
fi
if [ ! -f "$FRONTEND_DIR/.env" ]; then
  echo "✗ $FRONTEND_DIR/.env não encontrado. Rode: bash setup.sh <nome-do-banco>"
  exit 1
fi
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  echo "✗ .venv não encontrado. Rode: bash setup.sh <nome-do-banco>"
  exit 1
fi

echo ""
echo "Iniciando backend  → http://localhost:8000"
echo "Iniciando frontend → http://localhost:5173"
echo "Logs: /tmp/backend.log  e  /tmp/frontend.log"
echo "Para parar: Ctrl+C ou bash stop.sh"
echo ""

# para processos anteriores se existirem
kill $(lsof -ti:8000) 2>/dev/null || true
kill $(lsof -ti:5173) 2>/dev/null || true
sleep 1

# backend
(cd "$BACKEND_DIR" && .venv/bin/uvicorn api.main:app --reload --reload-dir api --reload-dir src --port 8000) > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# frontend
(cd "$FRONTEND_DIR" && npm run dev) > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# aguarda e mostra logs iniciais
sleep 3
echo ""
echo "--- Backend ---"
tail -5 /tmp/backend.log
echo ""
echo "--- Frontend ---"
tail -5 /tmp/frontend.log
echo ""
echo "Projeto rodando. Acesse http://localhost:5173"
