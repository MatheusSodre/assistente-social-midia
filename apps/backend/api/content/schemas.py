from pydantic import BaseModel, Field
from typing import Optional


class ContentGenerateRequest(BaseModel):
    business_id: str
    objective: str
    format: str = "post"
    tone: str = "profissional"
    audience: str = "geral"
    slide_count: int = Field(default=5, ge=2, le=10)


class BatchItem(BaseModel):
    objective: str
    format: str = "post"
    tone: str = "profissional"
    audience: str = "geral"


class BatchGenerateRequest(BaseModel):
    business_id: str
    items: list[BatchItem] = Field(..., max_length=7)
