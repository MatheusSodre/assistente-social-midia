from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.connection import init_db

from .auth.router import router as auth_router

# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from src.<dominio>.notificador import meu_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(meu_job, 'cron', hour=8, minute=0)
    # scheduler.start()

    yield

    # scheduler.shutdown()


app = FastAPI(title="Meu Projeto", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# app.include_router(meu_modulo_router)
