import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from src.engines.publisher.token_manager import encrypt_token
from .schemas import BusinessCreate, BusinessUpdate, InstagramConnect, AnalyzeUrlRequest

router = APIRouter(prefix="/api/v1/businesses", tags=["businesses"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _verify_ownership(business_id: str, usuario_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, usuario_id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Business não encontrado")
    return row


def _compute_readiness(business_id: str) -> dict[str, Any]:
    """Calcula score de prontidão do perfil do negócio (0-100)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM businesses WHERE id = %s", (business_id,))
            biz = cur.fetchone() or {}
            cur.execute("SELECT * FROM brand_strategy WHERE business_id = %s", (business_id,))
            strategy = cur.fetchone() or {}
            cur.execute("SELECT * FROM visual_identity WHERE business_id = %s", (business_id,))
            identity = cur.fetchone()

    def _has(val):
        if val is None:
            return False
        if isinstance(val, str):
            v = val.strip()
            if not v or v in ("[]", "{}", "null"):
                return False
            # JSON array check
            try:
                parsed = json.loads(v)
                if isinstance(parsed, (list, dict)) and len(parsed) == 0:
                    return False
            except Exception:
                pass
            return True
        if isinstance(val, (list, dict)):
            return len(val) > 0
        return True

    # Parse JSON fields from strategy
    for f in ["personas", "content_pillars", "posting_frequency", "brand_colors", "competitors", "goals"]:
        if strategy.get(f) and isinstance(strategy[f], str):
            try:
                strategy[f] = json.loads(strategy[f])
            except Exception:
                pass

    checks = [
        ("name", _has(biz.get("name")), 5, "Nome do negócio"),
        ("type", _has(biz.get("type")), 5, "Tipo/nicho"),
        ("description", _has(biz.get("description")), 15, "Descrição do negócio"),
        ("services", _has(biz.get("services")), 10, "Produtos ou serviços"),
        ("target_audience", _has(biz.get("target_audience")), 10, "Público-alvo"),
        ("online_presence", _has(biz.get("website_url")) or _has(biz.get("instagram_handle")), 5, "Site ou Instagram"),
        ("brand_tone", _has(strategy.get("brand_tone")), 10, "Tom de voz da marca"),
        ("content_pillars", _has(strategy.get("content_pillars")), 10, "Pilares de conteúdo"),
        ("goals", _has(strategy.get("goals")), 10, "Objetivos da estratégia"),
        ("differentials", _has(biz.get("differentials")), 10, "Diferenciais do negócio"),
        ("visual_identity", identity is not None, 10, "Identidade visual (cores e fontes)"),
    ]

    score = sum(weight for _, filled, weight, _ in checks if filled)
    missing = [{"field": field, "label": label, "weight": weight} for field, filled, weight, label in checks if not filled]

    return {
        "score": score,
        "ready": score >= 60,
        "missing": missing,
        "total_fields": len(checks),
        "filled_fields": len(checks) - len(missing),
    }


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("")
def create_business(data: BusinessCreate, user=Depends(get_current_user)) -> dict[str, Any]:
    bid = str(uuid.uuid4())
    now = datetime.utcnow()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO businesses
                   (id, usuario_id, name, type, description, location, website_url,
                    instagram_handle, linkedin_url, services, target_audience, differentials,
                    brand_context, criado_em, atualizado_em)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    bid, user["sub"], data.name, data.type,
                    data.description, data.location, data.website_url,
                    data.instagram_handle, data.linkedin_url,
                    json.dumps(data.services, ensure_ascii=False) if data.services else None,
                    data.target_audience, data.differentials,
                    json.dumps(data.brand_context) if data.brand_context else None,
                    now, now,
                ),
            )
    return {"id": bid, "name": data.name, "type": data.type}


@router.get("")
def list_businesses(user=Depends(get_current_user)) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, name, type, description, location, website_url, instagram_handle,
                          instagram_account_id, services, criado_em
                   FROM businesses WHERE usuario_id = %s ORDER BY criado_em DESC""",
                (user["sub"],),
            )
            rows = cur.fetchall()
    return rows or []


@router.get("/{business_id}")
def get_business(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    row = _verify_ownership(business_id, user["sub"])
    # Remove sensitive fields
    row.pop("instagram_access_token", None)
    return row


@router.put("/{business_id}")
def update_business(business_id: str, data: BusinessUpdate, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_ownership(business_id, user["sub"])

    fields = {}
    for key, val in data.model_dump(exclude_none=True).items():
        if key == "services":
            fields[key] = json.dumps(val, ensure_ascii=False) if val else None
        elif key == "brand_context":
            fields[key] = json.dumps(val, ensure_ascii=False) if val else None
        else:
            fields[key] = val

    if not fields:
        raise HTTPException(400, "Nenhum campo para atualizar")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [business_id]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE businesses SET {set_clause}, atualizado_em = NOW() WHERE id = %s",
                values,
            )

    return {"message": "Atualizado", "updated_fields": list(fields.keys())}


@router.delete("/{business_id}")
def delete_business(business_id: str, user=Depends(get_current_user)) -> dict[str, str]:
    _verify_ownership(business_id, user["sub"])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM businesses WHERE id = %s", (business_id,))
    return {"message": "Negócio excluído"}


# ─── Readiness ────────────────────────────────────────────────────────────────

@router.get("/{business_id}/readiness")
def readiness(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_ownership(business_id, user["sub"])
    return _compute_readiness(business_id)


# ─── Instagram ────────────────────────────────────────────────────────────────

@router.post("/{business_id}/connect-instagram")
async def connect_instagram(business_id: str, data: InstagramConnect, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_ownership(business_id, user["sub"])
    encrypted = encrypt_token(data.access_token)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE businesses SET instagram_account_id = %s, instagram_access_token = %s, atualizado_em = NOW() WHERE id = %s",
                (data.instagram_account_id, encrypted, business_id),
            )

    # Auto-análise do estilo do Instagram em background
    import asyncio
    async def _auto_analyze():
        try:
            from src.engines.intelligence.instagram_analyzer import analyze_instagram_style
            await analyze_instagram_style(business_id)
        except Exception:
            pass  # Silently fail — non-critical
    asyncio.create_task(_auto_analyze())

    return {"message": "Instagram conectado. Analisando estilo do feed...", "instagram_account_id": data.instagram_account_id}


@router.post("/{business_id}/analyze-instagram-style")
async def analyze_ig_style(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    """Analisa os posts existentes do Instagram para entender o estilo do feed."""
    _verify_ownership(business_id, user["sub"])
    from src.engines.intelligence.instagram_analyzer import analyze_instagram_style
    return await analyze_instagram_style(business_id)


# ─── Intelligence (scraping & analysis) ──────────────────────────────────────

@router.post("/{business_id}/analyze-url")
async def analyze_url(business_id: str, data: AnalyzeUrlRequest, user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_ownership(business_id, user["sub"])
    from src.engines.intelligence.web_scraper import analyze_website
    result = await analyze_website(data.url)
    if result.get("error"):
        raise HTTPException(400, result["error"])

    # Auto-merge extracted data into business profile
    _auto_merge(business_id, result)
    readiness_data = _compute_readiness(business_id)
    return {"extracted": result, "readiness": readiness_data}


@router.post("/{business_id}/upload-document")
async def upload_document(business_id: str, file: UploadFile = File(...), user=Depends(get_current_user)) -> dict[str, Any]:
    _verify_ownership(business_id, user["sub"])
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "Arquivo muito grande (máx 10MB)")

    from src.engines.intelligence.pdf_extractor import extract_from_pdf
    result = await extract_from_pdf(contents, file.filename or "document")
    if result.get("error"):
        raise HTTPException(400, result["error"])

    _auto_merge(business_id, result)
    readiness_data = _compute_readiness(business_id)
    return {"extracted": result, "readiness": readiness_data}


def _auto_merge(business_id: str, extracted: dict) -> None:
    """Merge extracted intelligence into business profile (only empty fields)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM businesses WHERE id = %s", (business_id,))
            biz = cur.fetchone() or {}

    updates = {}
    field_map = {
        "description": "description",
        "services": "services",
        "target_audience": "target_audience",
        "differentials": "differentials",
        "location": "location",
    }

    for ext_key, db_key in field_map.items():
        if extracted.get(ext_key) and not biz.get(db_key):
            val = extracted[ext_key]
            if isinstance(val, list):
                updates[db_key] = json.dumps(val, ensure_ascii=False)
            else:
                updates[db_key] = val

    # Merge brand_context (store raw intelligence)
    existing_ctx = biz.get("brand_context")
    if existing_ctx and isinstance(existing_ctx, str):
        try:
            existing_ctx = json.loads(existing_ctx)
        except Exception:
            existing_ctx = {}
    existing_ctx = existing_ctx or {}
    existing_ctx["_last_analysis"] = extracted
    updates["brand_context"] = json.dumps(existing_ctx, ensure_ascii=False)

    if updates:
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [business_id]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE businesses SET {set_clause}, atualizado_em = NOW() WHERE id = %s",
                    values,
                )

    # Auto-fill brand_strategy if extracted
    if extracted.get("brand_tone") or extracted.get("content_pillars") or extracted.get("goals"):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM brand_strategy WHERE business_id = %s", (business_id,))
                existing = cur.fetchone()

                strategy_updates = {}
                if extracted.get("brand_tone"):
                    strategy_updates["brand_tone"] = extracted["brand_tone"]
                if extracted.get("content_pillars"):
                    strategy_updates["content_pillars"] = json.dumps(extracted["content_pillars"], ensure_ascii=False)
                if extracted.get("goals"):
                    strategy_updates["goals"] = json.dumps(extracted["goals"], ensure_ascii=False)
                if extracted.get("colors"):
                    strategy_updates["brand_colors"] = json.dumps(extracted["colors"], ensure_ascii=False)

                if strategy_updates:
                    if existing:
                        set_parts = ", ".join(f"{k} = COALESCE(NULLIF({k}, ''), %s)" for k in strategy_updates)
                        cur.execute(
                            f"UPDATE brand_strategy SET {set_parts}, atualizado_em = NOW() WHERE business_id = %s",
                            list(strategy_updates.values()) + [business_id],
                        )
                    else:
                        sid = str(uuid.uuid4())
                        cols = ["id", "business_id"] + list(strategy_updates.keys())
                        vals = [sid, business_id] + list(strategy_updates.values())
                        cur.execute(
                            f"INSERT INTO brand_strategy ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                            vals,
                        )
