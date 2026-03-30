import os
from contextlib import contextmanager

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

from .schema import SCHEMA, MIGRATIONS

load_dotenv()


def _get_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "db_meu_projeto"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    }


@contextmanager
def get_connection():
    conn = pymysql.connect(**_get_config())
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Executa o DDL completo + migrations. Chamado no startup da aplicação."""
    statements = [s.strip() for s in SCHEMA.split(";") if s.strip()]
    with get_connection() as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)

    # Migrations para adicionar colunas em bancos existentes
    if MIGRATIONS:
        migration_stmts = [s.strip() for s in MIGRATIONS.split(";") if s.strip()]
        with get_connection() as conn:
            with conn.cursor() as cur:
                for stmt in migration_stmts:
                    try:
                        cur.execute(stmt)
                    except Exception:
                        pass  # coluna já existe ou statement irrelevante

    print("✓ Banco inicializado")
