from supabase import Client, create_client

from app.core.config import Settings


def build_supabase_admin_client(settings: Settings) -> Client:
    """Cliente com service_role — bypassa RLS, usado pra Storage e Auth admin."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class SupabaseStorage:
    """
    Wrapper sobre supabase-py Storage. Convenção de path:
        {bucket}/{tenant_id}/{generation_id}/{filename}
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def upload(
        self,
        *,
        bucket: str,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        upsert: bool = True,
    ) -> str:
        self._client.storage.from_(bucket).upload(
            path=path,
            file=data,
            file_options={"content-type": content_type, "upsert": str(upsert).lower()},
        )
        return path

    def signed_url(self, *, bucket: str, path: str, ttl_seconds: int = 3600) -> str:
        result = self._client.storage.from_(bucket).create_signed_url(path, ttl_seconds)
        return result["signedURL"] if isinstance(result, dict) else result.signed_url

    def remove(self, *, bucket: str, paths: list[str]) -> None:
        self._client.storage.from_(bucket).remove(paths)
