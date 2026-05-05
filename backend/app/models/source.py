from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    WEBSITE = "website"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    PDF = "pdf"
    CHAT = "chat"


class SourceStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class SourceCreate(BaseModel):
    type: SourceType
    name: str = Field(min_length=1, max_length=200)
    url_or_path: str = Field(min_length=1)
    added_via_chat: bool = False


class Source(BaseModel):
    id: UUID
    tenant_id: UUID
    type: SourceType
    name: str
    url_or_path: str
    status: SourceStatus
    items_count: int | None
    error_message: str | None
    metadata: dict[str, Any]
    added_by_user_id: UUID | None
    added_via_chat: bool
    last_indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime
