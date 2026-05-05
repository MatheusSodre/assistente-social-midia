"""Dependency providers que leem singletons do app.state."""
from fastapi import Request

from app.services.brand_block_service import BrandBlockService
from app.services.brand_memory_service import BrandMemoryService
from app.services.change_service import ChangeService
from app.services.generation_service import GenerationService
from app.services.lia_service import LiaService
from app.services.source_service import SourceService
from app.services.storage_service import StorageService
from app.services.template_service import TemplateService


def get_brand_service(request: Request) -> BrandMemoryService:
    return request.app.state.brand_service


def get_template_service(request: Request) -> TemplateService:
    return request.app.state.template_service


def get_generation_service(request: Request) -> GenerationService:
    return request.app.state.generation_service


def get_storage_service(request: Request) -> StorageService:
    return request.app.state.storage_service


def get_brand_block_service(request: Request) -> BrandBlockService:
    return request.app.state.brand_block_service


def get_change_service(request: Request) -> ChangeService:
    return request.app.state.change_service


def get_source_service(request: Request) -> SourceService:
    return request.app.state.source_service


def get_lia_service(request: Request) -> LiaService:
    return request.app.state.lia_service
