from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AgentLog(BaseModel):
    id: UUID
    generation_id: UUID
    agent_name: str
    model: str
    input: dict[str, Any]
    output: dict[str, Any]
    tokens_in: int
    tokens_out: int
    cost_cents: int
    latency_ms: int
    created_at: datetime
