"""
Compositor de imagens com Pillow.
Ferramentas: remover fundo, adicionar texto, aplicar identidade visual.
"""
import io
import logging
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def remove_background(image_bytes: bytes) -> bytes:
    """Remove o fundo da imagem usando rembg. Retorna PNG com fundo transparente."""
    from rembg import remove
    result = remove(image_bytes)
    logger.info({"event": "composer_remove_bg", "input_bytes": len(image_bytes), "output_bytes": len(result)})
    return result


def add_text_overlay(
    image_bytes: bytes,
    text: str,
    position: str = "bottom",  # top | bottom | center
    font_size: int = 48,
    text_color: str = "#FFFFFF",
    overlay_color: Optional[str] = "#000000",
    overlay_opacity: int = 140,  # 0-255
    padding: int = 24,
) -> bytes:
    """
    Adiciona texto sobre a imagem com faixa de fundo semi-transparente.
    Retorna JPEG.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    # Tenta usar fonte padrão do sistema; fallback para default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Mede o texto
    dummy = Image.new("RGBA", (1, 1))
    draw_dummy = ImageDraw.Draw(dummy)
    bbox = draw_dummy.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Faixa de overlay
    strip_h = text_h + padding * 2
    overlay = Image.new("RGBA", (w, strip_h), (0, 0, 0, 0))
    if overlay_color:
        r, g, b = _hex_to_rgb(overlay_color)
        overlay_layer = Image.new("RGBA", (w, strip_h), (r, g, b, overlay_opacity))
        overlay.paste(overlay_layer)

    # Posição da faixa
    if position == "top":
        strip_y = 0
    elif position == "center":
        strip_y = (h - strip_h) // 2
    else:  # bottom
        strip_y = h - strip_h

    img.paste(overlay, (0, strip_y), overlay)

    draw = ImageDraw.Draw(img)
    text_x = (w - text_w) // 2
    text_y = strip_y + padding

    # Sombra
    draw.text((text_x + 2, text_y + 2), text, font=font, fill=(0, 0, 0, 180))
    # Texto principal
    r, g, b = _hex_to_rgb(text_color)
    draw.text((text_x, text_y), text, font=font, fill=(r, g, b, 255))

    out = img.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def apply_brand_background(
    subject_bytes: bytes,
    bg_color: str = "#FFFFFF",
    canvas_size: tuple[int, int] = (1080, 1080),
    padding_pct: float = 0.1,
) -> bytes:
    """
    Cola o subject (imagem com fundo removido) sobre uma tela com cor da marca.
    Retorna JPEG.
    """
    r, g, b = _hex_to_rgb(bg_color)
    canvas = Image.new("RGBA", canvas_size, (r, g, b, 255))

    subject = Image.open(io.BytesIO(subject_bytes)).convert("RGBA")

    # Redimensiona mantendo proporção com padding
    pad = int(canvas_size[0] * padding_pct)
    max_w = canvas_size[0] - pad * 2
    max_h = canvas_size[1] - pad * 2
    subject.thumbnail((max_w, max_h), Image.LANCZOS)

    # Centraliza
    sx = (canvas_size[0] - subject.width) // 2
    sy = (canvas_size[1] - subject.height) // 2
    canvas.paste(subject, (sx, sy), subject)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte #RRGGBB para (r, g, b)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
