import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.finance_engine.pluggy_client import PluggyClient
from src.engines.finance_engine.analyzer import analyze_transactions
from .schemas import (
    AlertOut,
    AnalysisOut,
    ConnectionCreate,
    ConnectionOut,
    ConnectTokenResponse,
    TransactionOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/finance", tags=["finance"])


# ─── Connect Token ─────────────────────────────────────────────────────────────

@router.post("/connect-token", response_model=ConnectTokenResponse)
async def create_connect_token(user=Depends(get_current_user)) -> dict[str, Any]:
    client = PluggyClient()
    try:
        token = await client.create_connect_token(user["sub"])
    except Exception as exc:
        logger.error("Pluggy connect-token error: %s", exc)
        raise HTTPException(502, f"Erro ao gerar token Pluggy: {exc}")
    return {"connect_token": token}


# ─── Connections ───────────────────────────────────────────────────────────────

@router.post("/connections", response_model=ConnectionOut)
async def create_connection(data: ConnectionCreate, user=Depends(get_current_user)) -> dict[str, Any]:
    cid = str(uuid.uuid4())
    now = datetime.utcnow()

    # Tenta buscar nome do conector via Pluggy se não informado
    connector_name = data.connector_name
    if not connector_name:
        try:
            pluggy = PluggyClient()
            item = await pluggy.get_item(data.item_id)
            connector_name = item.get("connector", {}).get("name")
        except Exception:
            pass

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO finance_connections
                    (id, usuario_id, item_id, connector_name, status, created_at)
                VALUES (%s, %s, %s, %s, 'updating', %s)
                """,
                (cid, user["sub"], data.item_id, connector_name, now),
            )

    # Dispara sync assíncrono em background (fire-and-forget)
    try:
        await _sync_connection(cid, data.item_id, user["sub"])
    except Exception as exc:
        logger.warning("Initial sync failed for connection %s: %s", cid, exc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM finance_connections WHERE id = %s", (cid,))
            row = cur.fetchone()
    return row


@router.get("/connections", response_model=list[ConnectionOut])
def list_connections(user=Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM finance_connections WHERE usuario_id = %s ORDER BY created_at DESC",
                (user["sub"],),
            )
            return cur.fetchall() or []


@router.delete("/connections/{connection_id}")
def delete_connection(connection_id: str, user=Depends(get_current_user)) -> dict[str, str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM finance_connections WHERE id = %s AND usuario_id = %s",
                (connection_id, user["sub"]),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Conexão não encontrada")
            cur.execute("DELETE FROM finance_connections WHERE id = %s", (connection_id,))
    return {"message": "Conexão removida com sucesso"}


# ─── Transactions ──────────────────────────────────────────────────────────────

@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    user=Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
    tipo: Optional[str] = Query(None, description="CREDIT ou DEBIT"),
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
) -> list[dict[str, Any]]:
    since = (datetime.utcnow() - timedelta(days=days)).date()

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Pega connection_ids do usuário
            cur.execute(
                "SELECT id FROM finance_connections WHERE usuario_id = %s",
                (user["sub"],),
            )
            conn_ids = [r["id"] for r in (cur.fetchall() or [])]

    if not conn_ids:
        return []

    placeholders = ",".join(["%s"] * len(conn_ids))
    params: list = list(conn_ids)
    where_extra = ""

    if tipo:
        where_extra += " AND ft.type = %s"
        params.append(tipo.upper())
    if categoria:
        where_extra += " AND ft.category = %s"
        params.append(categoria)
    if busca:
        where_extra += " AND ft.description LIKE %s"
        params.append(f"%{busca}%")

    params.append(str(since))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ft.*
                FROM finance_transactions ft
                WHERE ft.connection_id IN ({placeholders})
                  {where_extra}
                  AND ft.date >= %s
                ORDER BY ft.date DESC
                LIMIT 500
                """,
                params,
            )
            return cur.fetchall() or []


# ─── Sync ──────────────────────────────────────────────────────────────────────

@router.post("/sync")
async def sync_all(user=Depends(get_current_user)) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, item_id FROM finance_connections WHERE usuario_id = %s",
                (user["sub"],),
            )
            connections = cur.fetchall() or []

    if not connections:
        return {"synced": 0, "errors": []}

    errors: list[str] = []
    synced = 0
    for conn_row in connections:
        try:
            await _sync_connection(conn_row["id"], conn_row["item_id"], user["sub"])
            synced += 1
        except Exception as exc:
            errors.append(f"{conn_row['id']}: {exc}")

    return {"synced": synced, "errors": errors}


# ─── Analysis ──────────────────────────────────────────────────────────────────

@router.get("/analysis", response_model=AnalysisOut)
async def get_analysis(user=Depends(get_current_user)) -> dict[str, Any]:
    since = (datetime.utcnow() - timedelta(days=30)).date()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM finance_connections WHERE usuario_id = %s",
                (user["sub"],),
            )
            conn_ids = [r["id"] for r in (cur.fetchall() or [])]

    if not conn_ids:
        return {
            "summary": "Nenhuma conta conectada. Conecte um banco para análise.",
            "top_categories": [],
            "insights": [],
            "recommendations": [],
        }

    placeholders = ",".join(["%s"] * len(conn_ids))
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT date, description, amount, type, category
                FROM finance_transactions
                WHERE connection_id IN ({placeholders}) AND date >= %s
                ORDER BY date DESC
                """,
                list(conn_ids) + [str(since)],
            )
            txs = cur.fetchall() or []

    # Converte Decimal → float para JSON serialization
    transactions_clean = [
        {**tx, "amount": float(tx["amount"]) if tx.get("amount") is not None else None}
        for tx in txs
    ]

    result = await analyze_transactions(transactions_clean)
    return result


# ─── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=list[AlertOut])
def get_alerts(user=Depends(get_current_user), days_ahead: int = Query(7, ge=1, le=30)) -> list[dict[str, Any]]:
    today = date.today()
    until = today + timedelta(days=days_ahead)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM finance_connections WHERE usuario_id = %s",
                (user["sub"],),
            )
            conn_ids = [r["id"] for r in (cur.fetchall() or [])]

    if not conn_ids:
        return []

    placeholders = ",".join(["%s"] * len(conn_ids))
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, description, amount, date, account_id
                FROM finance_transactions
                WHERE connection_id IN ({placeholders})
                  AND status = 'PENDING'
                  AND date BETWEEN %s AND %s
                ORDER BY date ASC
                """,
                list(conn_ids) + [str(today), str(until)],
            )
            rows = cur.fetchall() or []

    alerts = []
    for row in rows:
        tx_date = row["date"]
        days_until = (tx_date - today).days if tx_date else 0
        alerts.append({**row, "days_until_due": days_until})
    return alerts


# ─── Internal helpers ─────────────────────────────────────────────────────────

async def _sync_connection(connection_id: str, item_id: str, usuario_id: str) -> None:
    pluggy = PluggyClient()
    from_date = (datetime.utcnow() - timedelta(days=90)).date()
    to_date = datetime.utcnow().date()

    try:
        accounts = await pluggy.get_accounts(item_id)
    except Exception as exc:
        _mark_connection_error(connection_id)
        raise exc

    for account in accounts:
        account_id = account.get("id")
        if not account_id:
            continue
        try:
            txs = await pluggy.get_transactions(account_id, from_date, to_date)
        except Exception as exc:
            logger.warning("Failed to fetch transactions for account %s: %s", account_id, exc)
            continue

        for tx in txs:
            _upsert_transaction(connection_id, account_id, tx)

    # Marca como sincronizado
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE finance_connections SET status='updated', last_synced_at=NOW() WHERE id=%s",
                (connection_id,),
            )


def _mark_connection_error(connection_id: str) -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE finance_connections SET status='error' WHERE id=%s",
                    (connection_id,),
                )
    except Exception:
        pass


def _upsert_transaction(connection_id: str, account_id: str, tx: dict) -> None:
    pluggy_id = tx.get("id")
    tx_date = tx.get("date", "")[:10] if tx.get("date") else None
    description = (tx.get("description") or "")[:500]
    amount = tx.get("amount")
    tx_type = tx.get("type", "DEBIT")
    category = (tx.get("category") or tx.get("categoryId") or "")[:100] or None
    status = tx.get("status", "POSTED")

    tid = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor() as cur:
            if pluggy_id:
                cur.execute(
                    """
                    INSERT INTO finance_transactions
                        (id, connection_id, pluggy_id, account_id, date, description, amount, type, category, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        description=VALUES(description),
                        amount=VALUES(amount),
                        category=VALUES(category),
                        status=VALUES(status)
                    """,
                    (tid, connection_id, pluggy_id, account_id, tx_date, description, amount, tx_type, category, status),
                )
            else:
                cur.execute(
                    """
                    INSERT IGNORE INTO finance_transactions
                        (id, connection_id, pluggy_id, account_id, date, description, amount, type, category, status)
                    VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (tid, connection_id, account_id, tx_date, description, amount, tx_type, category, status),
                )
