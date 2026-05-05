"""Dependency providers que leem singletons do app.state."""
from fastapi import Request

from app.services.brand_memory_service import BrandMemoryService
from app.services.generation_service import GenerationService
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
