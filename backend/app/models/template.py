from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TemplateType(str, Enum):
    POST = "post"
    CAROUSEL_SLIDE = "carousel_slide"
    STORY = "story"


class Dimensions(BaseModel):
    width: int
    height: int


class Template(BaseModel):
    id: UUID
    name: str
    type: TemplateType
    dimensions: Dimensions
    slots: dict[str, Any] = Field(default_factory=dict)
    layout_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
