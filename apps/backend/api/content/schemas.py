from pydantic import BaseModel, Field
from typing import Optional


class ContentGenerateRequest(BaseModel):
    business_id: str
    objective: str
    format: str = "post"
    tone: str = "profissional"
    audience: str = "geral"


class BatchItem(BaseModel):
    objective: str
    format: str = "post"
    tone: str = "profissional"
    audience: str = "geral"


class BatchGenerateRequest(BaseModel):
    business_id: str
    items: list[BatchItem] = Field(..., max_length=7)
