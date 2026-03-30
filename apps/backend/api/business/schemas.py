from pydantic import BaseModel
from typing import Optional, Any


class BusinessCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    instagram_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    services: Optional[list[str]] = None
    target_audience: Optional[str] = None
    differentials: Optional[str] = None
    brand_context: Optional[dict[str, Any]] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    instagram_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    services: Optional[list[str]] = None
    target_audience: Optional[str] = None
    differentials: Optional[str] = None
    brand_context: Optional[dict[str, Any]] = None


class InstagramConnect(BaseModel):
    instagram_account_id: str
    access_token: str


class AnalyzeUrlRequest(BaseModel):
    url: str
