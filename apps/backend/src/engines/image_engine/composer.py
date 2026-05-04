"""
Compositor de imagens com Pillow.
Ferramentas: remover fundo, adicionar texto, aplicar identidade visual.
"""
import io
import logging
import os
import re
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Diretório de fontes customizadas
FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"


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


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Carrega fonte por nome com fallback."""
    # Tenta fonte customizada no diretório assets/fonts
    font_map = {
        "poppins-bold": "Poppins-Bold.ttf",
        "poppins": "Poppins-Regular.ttf",
        "inter": "Inter-Variable.ttf",
    }
    filename = font_map.get(name.lower(), f"{name}.ttf")
    custom_path = FONTS_DIR / filename
    if custom_path.exists():
        return ImageFont.truetype(str(custom_path), size)

    # Fallback para fontes do sistema
    system_fallbacks = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for fb in system_fallbacks:
        if os.path.exists(fb):
            return ImageFont.truetype(fb, size)

    return ImageFont.load_default()


def compose_branded_slide(
    image_bytes: bytes,
    text: str,
    highlights: list[str] | None = None,
    accent_color: str = "#FF6B35",
    text_color: str = "#FFFFFF",
    overlay_color: str = "#0a0e27",
    overlay_opacity: int = 180,
    font_name: str = "poppins-bold",
    font_size: int = 64,
    position: str = "center",
    canvas_size: tuple[int, int] = (1080, 1080),
) -> bytes:
    """
    Cria slide de carousel com imagem de fundo, overlay escuro e texto em PT
    com palavras destacadas em cor de acento.

    Args:
        image_bytes: Imagem de fundo (gerada por IA)
        text: Texto principal em português (pode ter \\n)
        highlights: Lista de palavras/frases a destacar em accent_color
        accent_color: Cor de destaque (hex)
        text_color: Cor do texto principal (hex)
        overlay_color: Cor do overlay sobre a imagem (hex)
        overlay_opacity: Opacidade do overlay (0-255)
        font_name: Nome da fonte (poppins-bold, inter, etc)
        font_size: Tamanho da fonte
        position: Posição do texto (top, center, bottom)
        canvas_size: Tamanho final da imagem
    """
    # Abre e redimensiona imagem de fundo
    bg = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    bg = bg.resize(canvas_size, Image.LANCZOS)

    # Aplica overlay escuro
    r, g, b = _hex_to_rgb(overlay_color)
    overlay = Image.new("RGBA", canvas_size, (r, g, b, overlay_opacity))
    bg = Image.alpha_composite(bg, overlay)

    draw = ImageDraw.Draw(bg)
    font = _load_font(font_name, font_size)

    # Calcula posição do bloco de texto
    lines = text.split("\n")
    line_bboxes = []
    total_h = 0
    line_spacing = int(font_size * 0.35)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        line_bboxes.append((lw, lh))
        total_h += lh + line_spacing
    total_h -= line_spacing  # remove último spacing

    # Posição Y inicial
    pad = int(canvas_size[1] * 0.08)
    if position == "top":
        start_y = pad
    elif position == "bottom":
        start_y = canvas_size[1] - total_h - pad
    else:  # center
        start_y = (canvas_size[1] - total_h) // 2

    # Renderiza cada linha
    accent_rgb = _hex_to_rgb(accent_color)
    text_rgb = _hex_to_rgb(text_color)
    cur_y = start_y

    for i, line in enumerate(lines):
        lw, lh = line_bboxes[i]
        x = (canvas_size[0] - lw) // 2

        # Sombra
        draw.text((x + 3, cur_y + 3), line, font=font, fill=(0, 0, 0, 200))

        # Renderiza com highlights: desenha a linha inteira em branco, depois
        # sobrepõe as palavras destacadas em accent_color
        draw.text((x, cur_y), line, font=font, fill=(*text_rgb, 255))

        if highlights:
            for hl in highlights:
                if hl in line:
                    # Calcula offset X da palavra destacada dentro da linha
                    idx = line.index(hl)
                    prefix = line[:idx]
                    prefix_bbox = draw.textbbox((0, 0), prefix, font=font)
                    prefix_w = prefix_bbox[2] - prefix_bbox[0]

                    hl_x = x + prefix_w
                    # Sombra do highlight
                    draw.text((hl_x + 3, cur_y + 3), hl, font=font, fill=(0, 0, 0, 200))
                    draw.text((hl_x, cur_y), hl, font=font, fill=(*accent_rgb, 255))

        cur_y += lh + line_spacing

    # Converte e salva
    out = bg.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte #RRGGBB para (r, g, b)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
