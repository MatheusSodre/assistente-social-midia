from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GenerationStatus(str, Enum):
    PENDING = "pending"
    BRAND_LOADING = "brand_loading"
    CONTENT_GENERATING = "content_generating"
    IMAGE_GENERATING = "image_generating"
    VALIDATING = "validating"
    DONE = "done"
    FAILED = "failed"


class GenerationCreate(BaseModel):
    brief: str
    template_id: UUID | None = None


class GenerationResult(BaseModel):
    caption: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    headline: str | None = None
    visual_brief: str | None = None
    background_path: str | None = None
    background_url: str | None = None
    brand_review: dict[str, Any] | None = None
    error: str | None = None


class Generation(BaseModel):
    id: UUID
    tenant_id: UUID
    brief: str
    template_id: UUID | None
    status: GenerationStatus
    result: GenerationResult
    cost_cents: int
    created_by: UUID
    created_at: datetime
    completed_at: datetime | None
