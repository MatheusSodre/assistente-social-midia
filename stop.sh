#!/usr/bin/env bash
# Para backend e frontend
kill $(lsof -ti:8000) 2>/dev/null && echo "✓ Backend parado" || echo "→ Backend não estava rodando"
kill $(lsof -ti:5173) 2>/dev/null && echo "✓ Frontend parado" || echo "→ Frontend não estava rodando"
