import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))


def save_image_locally(image_bytes: bytes, format: str = "post", ext: str = "jpg") -> str:
    """Salva imagem localmente e retorna URL relativa. Fallback quando R2/S3 não está configurado."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(image_bytes)
    return f"/uploads/{filename}"


async def upload_image(image_bytes: bytes, format: str = "post", ext: str = "jpg") -> str:
    """Upload de imagem para storage. Tenta R2, fallback para local."""
    r2_bucket = os.getenv("R2_BUCKET")
    if r2_bucket:
        try:
            return await _upload_to_r2(image_bytes, format, ext)
        except Exception as e:
            logger.warning({"event": "r2_upload_failed", "error": str(e), "fallback": "local"})

    return save_image_locally(image_bytes, format, ext)


async def upload_carousel_images(
    images_bytes: list[bytes], format: str = "post", ext: str = "jpg"
) -> list[str]:
    """Upload de múltiplas imagens (carrossel). Retorna lista de URLs."""
    import asyncio
    tasks = [upload_image(img, format, ext) for img in images_bytes]
    return await asyncio.gather(*tasks)


async def _upload_to_r2(image_bytes: bytes, format: str, ext: str = "jpg") -> str:
    """Upload para Cloudflare R2 via boto3-compatible SDK."""
    import boto3
    import uuid

    content_type = "image/png" if ext == "png" else "image/jpeg"
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    )
    bucket = os.getenv("R2_BUCKET")
    key = f"images/{uuid.uuid4()}.{ext}"
    s3.put_object(Bucket=bucket, Key=key, Body=image_bytes, ContentType=content_type)
    return f"https://pub.{os.getenv('R2_ACCOUNT_ID')}.r2.dev/{key}"
