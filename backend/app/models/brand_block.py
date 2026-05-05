from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError


class BlockKey(str, Enum):
    BRAND = "brand"
    ICP = "icp"
    TONE = "tone"
    VISUAL = "visual"
    TOPICS = "topics"
    COMPETITORS = "competitors"
    EXAMPLES = "examples"


class BlockStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    EMPTY = "empty"


class ChangeSourceType(str, Enum):
    MANUAL = "manual"
    SESSION = "session"
    CASCADE = "cascade"
    INGESTION = "ingestion"
    LIA = "lia"
    SYSTEM = "system"


# ============================================================================
# Schemas POR BLOCO — validação semântica do conteúdo jsonb
# ============================================================================
# jsonb no banco é livre, mas Pydantic valida no caminho de entrada.
# Cada bloco tem schema próprio. Se vier conteúdo fora do schema, 422.

class BrandContent(BaseModel):
    name: str | None = None
    positioning: str | None = None
    pillars: list[str] = Field(default_factory=list)


class IcpPersona(BaseModel):
    name: str
    role: str | None = None
    pains: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class IcpContent(BaseModel):
    personas: list[IcpPersona] = Field(default_factory=list)


class ToneContent(BaseModel):
    style: str | None = None
    do: list[str] = Field(default_factory=list)
    dont: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class VisualContent(BaseModel):
    primary_color: str | None = None
    secondary_color: str | None = None
    fonts: list[str] = Field(default_factory=list)
    logo_url: str | None = None
    style_description: str | None = None
    swatches: list[str] = Field(default_factory=list)


class TopicsContent(BaseModel):
    pillars: list[str] = Field(default_factory=list)
    notes: str | None = None


class CompetitorEntry(BaseModel):
    name: str
    handle: str | None = None
    notes: str | None = None


class CompetitorsContent(BaseModel):
    items: list[CompetitorEntry] = Field(default_factory=list)


class ExampleEntry(BaseModel):
    caption: str | None = None
    image_url: str | None = None
    why_it_works: str | None = None


class ExamplesContent(BaseModel):
    items: list[ExampleEntry] = Field(default_factory=list)


# Map block_key -> schema. Service usa pra validar antes de gravar.
BLOCK_CONTENT_SCHEMAS: dict[BlockKey, type[BaseModel]] = {
    BlockKey.BRAND: BrandContent,
    BlockKey.ICP: IcpContent,
    BlockKey.TONE: ToneContent,
    BlockKey.VISUAL: VisualContent,
    BlockKey.TOPICS: TopicsContent,
    BlockKey.COMPETITORS: CompetitorsContent,
    BlockKey.EXAMPLES: ExamplesContent,
}


def validate_block_content(block_key: BlockKey, content: dict[str, Any]) -> dict[str, Any]:
    """Valida content contra schema do bloco. Retorna dict normalizado.
    Erros de schema viram HTTP 422 (em vez de 500) ao subir até a request."""
    schema = BLOCK_CONTENT_SCHEMAS[block_key]
    try:
        validated = schema.model_validate(content)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    return validated.model_dump(exclude_none=False)


# ============================================================================
# DB models (read-side)
# ============================================================================

class BrandBlockVersion(BaseModel):
    id: UUID
    block_id: UUID
    version_number: int
    content: dict[str, Any]
    source_type: ChangeSourceType
    source_ref: str | None
    created_by: UUID | None
    created_by_agent: str | None
    reason: str | None
    created_at: datetime


class BrandBlock(BaseModel):
    id: UUID
    tenant_id: UUID
    block_key: BlockKey
    current_version_id: UUID | None
    status: BlockStatus
    confidence: int
    source_label: str | None
    content: dict[str, Any] | None  # join na version atual
    version_number: int | None
    created_at: datetime
    updated_at: datetime


class BrandMemoryDashboard(BaseModel):
    """Estrutura completa que o /api/v1/brand-memory devolve no MVP."""
    blocks: list[BrandBlock]
    total_blocks: int = 7
    completion_pct: int  # média ponderada de confidence
    pending_changes_count: int
