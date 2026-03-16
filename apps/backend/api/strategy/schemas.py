from pydantic import BaseModel
from typing import Optional, Any


class BrandStrategyUpdate(BaseModel):
    personas: Optional[list[dict[str, Any]]] = None
    content_pillars: Optional[list[str]] = None
    posting_frequency: Optional[dict[str, Any]] = None
    brand_tone: Optional[str] = None
    brand_colors: Optional[list[str]] = None
    competitors: Optional[list[str]] = None
    goals: Optional[list[str]] = None
