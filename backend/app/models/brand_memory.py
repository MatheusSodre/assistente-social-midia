from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Persona(BaseModel):
    name: str
    role: str | None = None
    pains: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class ToneOfVoice(BaseModel):
    style: str | None = None
    do: list[str] = Field(default_factory=list)
    dont: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class VisualIdentity(BaseModel):
    primary_color: str | None = None
    secondary_color: str | None = None
    fonts: list[str] = Field(default_factory=list)
    logo_url: str | None = None
    style_description: str | None = None


class Competitor(BaseModel):
    name: str
    handle: str | None = None
    notes: str | None = None


class Example(BaseModel):
    caption: str | None = None
    image_url: str | None = None
    why_it_works: str | None = None


class BrandMemoryBase(BaseModel):
    name: str
    positioning: str | None = None
    icp: list[Persona] = Field(default_factory=list)
    tone_of_voice: ToneOfVoice = Field(default_factory=ToneOfVoice)
    visual_identity: VisualIdentity = Field(default_factory=VisualIdentity)
    pillars: list[str] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    examples: list[Example] = Field(default_factory=list)


class BrandMemoryCreate(BrandMemoryBase):
    pass


class BrandMemoryUpdate(BaseModel):
    name: str | None = None
    positioning: str | None = None
    icp: list[Persona] | None = None
    tone_of_voice: ToneOfVoice | None = None
    visual_identity: VisualIdentity | None = None
    pillars: list[str] | None = None
    competitors: list[Competitor] | None = None
    examples: list[Example] | None = None


class BrandMemory(BrandMemoryBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
