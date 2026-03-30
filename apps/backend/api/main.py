import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from src.db.connection import init_db

from .auth.router import router as auth_router
from .business.router import router as business_router
from .content.router import router as content_router
from .schedule.router import router as schedule_router
from .posts.router import router as posts_router
from .strategy.router import router as strategy_router
from .agent.router import router as agent_router
from .ads.router import router as ads_router
from .designer.router import router as designer_router
from .finance.router import router as finance_router
from .agency.router import router as agency_router

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Cria usuário dev se não existir (login desabilitado)
    _ensure_dev_user()
    # Cria diretório de uploads local
    upload_dir = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    yield


def _ensure_dev_user():
    from src.db.connection import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM usuarios WHERE id = 'dev-user-001'")
            if not cur.fetchone():
                cur.execute(
                    """INSERT INTO usuarios (id, nome, email, google_sub, plano, role)
                       VALUES ('dev-user-001', 'Dev User', 'dev@local.dev', 'dev-local', 'profissional', 'admin')"""
                )
                print("✓ Usuário dev criado")


app = FastAPI(
    title="Assistente Multimídia Social",
    description="API para automação de redes sociais com IA generativa",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploads locais
upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
Path(upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(content_router)
app.include_router(schedule_router)
app.include_router(posts_router)
app.include_router(strategy_router)
app.include_router(agent_router)
app.include_router(ads_router)
app.include_router(designer_router)
app.include_router(finance_router)
app.include_router(agency_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "assistente-social-midia"}
