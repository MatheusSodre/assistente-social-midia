from pydantic import BaseModel
from typing import Optional, Any


class BusinessCreate(BaseModel):
    name: str
    type: str
    brand_context: Optional[dict[str, Any]] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    brand_context: Optional[dict[str, Any]] = None


class InstagramConnect(BaseModel):
    instagram_account_id: str
    access_token: str
