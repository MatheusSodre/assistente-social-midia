from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    IMAGE_PNG = "image_png"
    CAROUSEL_ZIP = "carousel_zip"
    COPY_TEXT = "copy_text"


class Asset(BaseModel):
    id: UUID
    generation_id: UUID
    type: AssetType
    storage_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
