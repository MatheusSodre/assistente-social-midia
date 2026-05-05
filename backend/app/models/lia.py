from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LiaMessageRole(str, Enum):
    USER = "user"
    LIA = "lia"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class LiaConversation(BaseModel):
    id: UUID
    tenant_id: UUID
    started_by_user_id: UUID
    title: str | None
    summary: str | None
    message_count: int
    total_cost_cents: int
    last_message_at: datetime | None
    created_at: datetime
    closed_at: datetime | None


class LiaMessage(BaseModel):
    id: UUID
    conversation_id: UUID
    role: LiaMessageRole
    content: str | None
    tool_name: str | None
    tool_input: dict[str, Any] | None
    tool_use_id: str | None
    tool_result: dict[str, Any] | None
    model: str | None
    tokens_in: int
    tokens_out: int
    cost_cents: int
    latency_ms: int | None
    created_at: datetime


class LiaConversationCreate(BaseModel):
    """Body pra POST /api/v1/lia/conversations."""
    pass  # backend cria com defaults — title/summary geram depois
