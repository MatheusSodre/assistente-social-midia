from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.brand_block import BlockKey, ChangeSourceType


class PendingChangeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class CascadeHint(BaseModel):
    block_key: BlockKey
    hint: str  # texto humano explicando a sugestão


class PendingChangeCreate(BaseModel):
    """Payload pra propor mudança via API ou agente."""
    block_key: BlockKey
    proposed_content: dict[str, Any]
    reason: str = Field(max_length=200)
    source_type: ChangeSourceType
    source_label: str
    source_ref: str | None = None
    proposed_by_agent: str | None = None  # 'lia', 'vega', etc.


class PendingChange(BaseModel):
    id: UUID
    tenant_id: UUID
    block_id: UUID
    block_key: BlockKey  # join
    proposed_by_user_id: UUID | None
    proposed_by_agent: str | None
    source_type: ChangeSourceType
    source_label: str
    source_ref: str | None
    from_version_id: UUID | None
    from_version_number: int | None  # join
    from_content: dict[str, Any] | None  # join
    proposed_content: dict[str, Any]
    reason: str
    cascades: list[CascadeHint]
    status: PendingChangeStatus
    resolved_by_user_id: UUID | None
    resolved_at: datetime | None
    created_at: datetime
