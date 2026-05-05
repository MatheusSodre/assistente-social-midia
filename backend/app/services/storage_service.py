"""
Composição de funções sobre SupabaseStorage:
- Upload de mídia
- Geração de signed URLs
- Empacotamento ZIP de carrossel (stdlib zipfile, sem dep extra)
"""
import io
import json
import zipfile
from typing import Iterable
from uuid import UUID

from app.integrations.supabase_client import SupabaseStorage


class StorageService:
    BUCKET_BRAND = "mkt-brand-assets"
    BUCKET_GENERATIONS = "mkt-generations"
    BUCKET_EXPORTS = "mkt-exports"

    def __init__(self, storage: SupabaseStorage) -> None:
        self._storage = storage

    # ------------------------------------------------------------------ paths
    @staticmethod
    def background_path(tenant_id: UUID, generation_id: UUID) -> str:
        return f"{tenant_id}/{generation_id}/background.png"

    @staticmethod
    def carousel_zip_path(tenant_id: UUID, generation_id: UUID) -> str:
        return f"{tenant_id}/{generation_id}/carousel.zip"

    @staticmethod
    def copy_text_path(tenant_id: UUID, generation_id: UUID) -> str:
        return f"{tenant_id}/{generation_id}/copy.txt"

    # ----------------------------------------------------------------- uploads
    def upload_background(
        self, *, tenant_id: UUID, generation_id: UUID, png_bytes: bytes
    ) -> str:
        path = self.background_path(tenant_id, generation_id)
        self._storage.upload(
            bucket=self.BUCKET_GENERATIONS,
            path=path,
            data=png_bytes,
            content_type="image/png",
        )
        return path

    def upload_brand_asset(
        self, *, tenant_id: UUID, filename: str, data: bytes, content_type: str
    ) -> str:
        path = f"{tenant_id}/{filename}"
        self._storage.upload(
            bucket=self.BUCKET_BRAND,
            path=path,
            data=data,
            content_type=content_type,
        )
        return path

    # --------------------------------------------------------------- exports
    def build_carousel_zip(
        self,
        *,
        tenant_id: UUID,
        generation_id: UUID,
        slide_pngs: Iterable[tuple[str, bytes]],
    ) -> str:
        """slide_pngs: iterable de (filename, png_bytes). Empacota em ZIP e
        sobe pra mkt-exports/{tenant}/{generation}/carousel.zip."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for filename, data in slide_pngs:
                zf.writestr(filename, data)
        path = self.carousel_zip_path(tenant_id, generation_id)
        self._storage.upload(
            bucket=self.BUCKET_EXPORTS,
            path=path,
            data=buf.getvalue(),
            content_type="application/zip",
        )
        return path

    def build_copy_text(
        self,
        *,
        tenant_id: UUID,
        generation_id: UUID,
        caption: str,
        hashtags: list[str],
    ) -> str:
        text = caption.rstrip() + "\n\n" + " ".join(hashtags)
        path = self.copy_text_path(tenant_id, generation_id)
        self._storage.upload(
            bucket=self.BUCKET_EXPORTS,
            path=path,
            data=text.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        return path

    # ------------------------------------------------------------ signed URL
    def signed_url(self, *, bucket: str, path: str, ttl_seconds: int = 3600) -> str:
        return self._storage.signed_url(bucket=bucket, path=path, ttl_seconds=ttl_seconds)
