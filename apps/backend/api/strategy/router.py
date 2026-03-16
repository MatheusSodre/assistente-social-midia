import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from api.auth.dependencies import get_current_user
from src.db.connection import get_connection
from .schemas import BrandStrategyUpdate

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


def _get_business(business_id: str, usuario_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM businesses WHERE id = %s AND usuario_id = %s",
                (business_id, usuario_id),
            )
            return cur.fetchone()


@router.get("/{business_id}")
def get_strategy(business_id: str, user=Depends(get_current_user)) -> dict[str, Any]:
    if not _get_business(business_id, user["sub"]):
        raise HTTPException(404, "Business não encontrado")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM brand_strategy WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()

    if not row:
        return {"business_id": business_id}

    json_fields = ["personas", "content_pillars", "posting_frequency", "brand_colors", "competitors", "goals"]
    for field in json_fields:
        if row.get(field) and isinstance(row[field], str):
            row[field] = json.loads(row[field])
    return row


@router.put("/{business_id}")
def upsert_strategy(
    business_id: str,
    data: BrandStrategyUpdate,
    user=Depends(get_current_user),
) -> dict[str, Any]:
    if not _get_business(business_id, user["sub"]):
        raise HTTPException(404, "Business não encontrado")

    fields = data.model_dump(exclude_none=True)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM brand_strategy WHERE business_id = %s",
                (business_id,),
            )
            existing = cur.fetchone()

            json_fields = ["personas", "content_pillars", "posting_frequency", "brand_colors", "competitors", "goals"]

            if existing:
                if not fields:
                    return {"business_id": business_id, "message": "Nenhuma alteração"}
                set_parts = []
                params = []
                for k, v in fields.items():
                    set_parts.append(f"{k} = %s")
                    params.append(json.dumps(v, ensure_ascii=False) if k in json_fields else v)
                params.append(business_id)
                cur.execute(
                    f"UPDATE brand_strategy SET {', '.join(set_parts)}, atualizado_em = NOW() WHERE business_id = %s",
                    params,
                )
            else:
                strategy_id = str(uuid.uuid4())
                col_names = ["id", "business_id"] + list(fields.keys())
                placeholders = ["%s"] * len(col_names)
                values = [strategy_id, business_id] + [
                    json.dumps(v, ensure_ascii=False) if k in json_fields else v
                    for k, v in fields.items()
                ]
                cur.execute(
                    f"INSERT INTO brand_strategy ({', '.join(col_names)}) VALUES ({', '.join(placeholders)})",
                    values,
                )

    return {"business_id": business_id, "message": "Estratégia salva com sucesso", **fields}
