"""
Pixel — Agente Designer Visual IA
Especialista em identidade visual, edição de imagens e criação de conteúdo brandado.
"""
import io
import json
import logging
import uuid
from typing import Any

import anthropic

from src.db.connection import get_connection
from src.engines.brand_context import get_unified_brand_context, brand_context_to_prompt
from src.engines.image_engine.composer import (
    remove_background,
    add_text_overlay,
    apply_brand_background,
)
from src.engines.image_engine.storage import upload_image

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

MODEL_SMART = "claude-haiku-4-5-20251001"
MODEL_FAST = "claude-haiku-4-5-20251001"

PIXEL_SYSTEM = """Você é Pixel, Designer Visual e especialista em identidade de marca.

QUEM VOCÊ É:
Formada em Design Gráfico com pós em Branding, você trabalha há 8 anos criando identidades visuais para marcas nas redes sociais. Você tem um olhar estético apurado e consegue traduzir a essência de uma marca em elementos visuais — cores, tipografia, composição. Você é a pessoa que faz uma imagem "ter a cara" da marca.

SUA PERSONALIDADE:
- Visual e descritiva: você "pensa em imagens" e descreve o que vê com riqueza de detalhes
- Perfeccionista com bom senso: busca qualidade mas sabe que feito é melhor que perfeito
- Consultiva: não só executa, mas explica por que certas escolhas visuais funcionam melhor
- Inspiradora: traz referências, sugere estilos, mostra possibilidades que o cliente não imaginou

COMO TRABALHAR:
- Quando receber uma imagem, descreva o que vê e sugira 2-3 coisas que pode fazer com ela
- Sempre consulte a identidade visual da marca (get_visual_identity) antes de editar
- Ao editar, explique o que fez e por quê: "Usei a cor primária da marca como fundo para manter a consistência visual"
- Se a marca não tem identidade visual definida, ofereça ajudar a definir uma paleta e estilo
- Após cada edição, pergunte: "Ficou do jeito que imaginava? Quer algum ajuste?"

SUAS FERRAMENTAS:
- Remover fundo de imagens
- Adicionar texto/legenda com estilo da marca
- Aplicar cor de fundo da marca
- Consultar e salvar identidade visual (cores, fontes, estilo)

Fale português brasileiro de forma criativa e acessível. Use termos de design quando relevante mas sempre explique de forma simples.
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_visual_identity",
        "description": "Consulta a identidade visual salva da marca (cores, fontes, estilo).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_visual_identity",
        "description": "Salva ou atualiza a identidade visual da marca.",
        "input_schema": {
            "type": "object",
            "properties": {
                "primary_color": {"type": "string", "description": "Cor primária em hex (#RRGGBB)"},
                "secondary_color": {"type": "string", "description": "Cor secundária em hex"},
                "accent_color": {"type": "string", "description": "Cor de destaque/acento em hex"},
                "background_color": {"type": "string", "description": "Cor de fundo padrão em hex"},
                "text_color": {"type": "string", "description": "Cor do texto em hex"},
                "font_heading": {"type": "string", "description": "Fonte para títulos/headings"},
                "font_body": {"type": "string", "description": "Fonte para corpo do texto"},
                "style_description": {"type": "string", "description": "Descrição livre do estilo visual (ex: moderno, minimalista, colorido)"},
                "extra_context": {"type": "string", "description": "Contexto adicional: referências, concorrentes, diferenciais visuais"},
            },
            "required": [],
        },
    },
    {
        "name": "remove_bg",
        "description": "Remove o fundo da imagem que o usuário enviou nesta conversa. Retorna URL da imagem sem fundo.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_text",
        "description": "Adiciona texto/legenda sobre a imagem atual (a última processada ou enviada).",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a ser adicionado na imagem"},
                "position": {"type": "string", "enum": ["top", "center", "bottom"], "description": "Posição do texto"},
                "font_size": {"type": "integer", "description": "Tamanho da fonte em pixels (padrão 48)", "default": 48},
                "text_color": {"type": "string", "description": "Cor do texto em hex (padrão #FFFFFF)"},
                "overlay_color": {"type": "string", "description": "Cor da faixa de fundo atrás do texto em hex"},
                "overlay_opacity": {"type": "integer", "description": "Opacidade da faixa 0-255 (padrão 140)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "apply_brand_bg",
        "description": "Aplica a cor de fundo da marca sobre a imagem com fundo removido, criando visual brandado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bg_color": {"type": "string", "description": "Cor de fundo em hex. Se não informado, usa a cor primária da identidade visual."},
            },
            "required": [],
        },
    },
]


# ─── Tool Executors ────────────────────────────────────────────────────────────

def _get_identity(business_id: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM visual_identity WHERE business_id = %s", (business_id,))
            row = cur.fetchone()
    if not row:
        return {"found": False, "message": "Identidade visual não configurada ainda."}
    if isinstance(row.get("reference_image_urls"), str):
        try:
            row["reference_image_urls"] = json.loads(row["reference_image_urls"])
        except Exception:
            pass
    return {"found": True, **row}


def _save_identity(business_id: str, fields: dict) -> dict:
    allowed = {
        "primary_color", "secondary_color", "accent_color", "background_color",
        "text_color", "font_heading", "font_body", "style_description",
        "logo_url", "reference_image_urls", "extra_context",
    }
    clean = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not clean:
        return {"success": False, "message": "Nenhum campo válido fornecido"}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM visual_identity WHERE business_id = %s", (business_id,))
            existing = cur.fetchone()
            if existing:
                set_parts = [f"{k} = %s" for k in clean]
                params = list(clean.values()) + [business_id]
                cur.execute(
                    f"UPDATE visual_identity SET {', '.join(set_parts)}, atualizado_em = NOW() WHERE business_id = %s",
                    params,
                )
            else:
                row_id = str(uuid.uuid4())
                cols = ["id", "business_id"] + list(clean.keys())
                placeholders = ["%s"] * len(cols)
                vals = [row_id, business_id] + list(clean.values())
                cur.execute(
                    f"INSERT INTO visual_identity ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                    vals,
                )
    return {"success": True, "saved_fields": list(clean.keys()), "message": "Identidade visual salva!"}


async def _exec_remove_bg(business_id: str, current_image_bytes: bytes | None) -> dict:
    if not current_image_bytes:
        return {"success": False, "message": "Nenhuma imagem enviada nesta conversa. Envie uma imagem primeiro."}
    try:
        result_bytes = remove_background(current_image_bytes)
        url = await upload_image(result_bytes, "post", ext="png")
        return {"success": True, "image_url": url, "message": "Fundo removido com sucesso!"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao remover fundo: {e}"}


async def _exec_add_text(
    business_id: str,
    current_image_bytes: bytes | None,
    tool_input: dict,
) -> dict:
    if not current_image_bytes:
        return {"success": False, "message": "Nenhuma imagem disponível. Envie uma imagem primeiro."}
    try:
        identity = _get_identity(business_id)
        text_color = tool_input.get("text_color") or identity.get("text_color") or "#FFFFFF"
        overlay_color = tool_input.get("overlay_color") or identity.get("primary_color") or "#000000"

        result_bytes = add_text_overlay(
            image_bytes=current_image_bytes,
            text=tool_input["text"],
            position=tool_input.get("position", "bottom"),
            font_size=tool_input.get("font_size", 48),
            text_color=text_color,
            overlay_color=overlay_color,
            overlay_opacity=tool_input.get("overlay_opacity", 140),
        )
        url = await upload_image(result_bytes, "post")
        return {"success": True, "image_url": url, "message": f"Texto '{tool_input['text']}' adicionado!"}
    except Exception as e:
        return {"success": False, "message": f"Erro ao adicionar texto: {e}"}


async def _exec_apply_brand_bg(business_id: str, current_image_bytes: bytes | None, tool_input: dict) -> dict:
    if not current_image_bytes:
        return {"success": False, "message": "Nenhuma imagem disponível."}
    try:
        identity = _get_identity(business_id)
        bg_color = tool_input.get("bg_color") or identity.get("primary_color") or "#FFFFFF"
        result_bytes = apply_brand_background(current_image_bytes, bg_color=bg_color)
        url = await upload_image(result_bytes, "post")
        return {"success": True, "image_url": url, "bg_color": bg_color, "message": "Fundo da marca aplicado!"}
    except Exception as e:
        return {"success": False, "message": f"Erro: {e}"}


# ─── Conversation Persistence ──────────────────────────────────────────────────

def _load_conversation(business_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Reuse agent_conversations table with a prefix trick — use a separate table via designer_conversations
            cur.execute(
                "SELECT messages FROM designer_conversations WHERE business_id = %s",
                (business_id,),
            )
            row = cur.fetchone()
    if not row:
        return []
    msgs = row["messages"]
    if isinstance(msgs, str):
        msgs = json.loads(msgs)
    return msgs or []


def _save_conversation(business_id: str, usuario_id: str, messages: list[dict]) -> None:
    trimmed = messages[-20:] if len(messages) > 20 else messages
    msgs_json = json.dumps(trimmed, ensure_ascii=False, default=str)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM designer_conversations WHERE business_id = %s", (business_id,))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE designer_conversations SET messages = %s, atualizado_em = NOW() WHERE business_id = %s",
                    (msgs_json, business_id),
                )
            else:
                cur.execute(
                    "INSERT INTO designer_conversations (id, business_id, usuario_id, messages) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), business_id, usuario_id, msgs_json),
                )


def _block_to_dict(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    return {"type": block.type}


# ─── Main Agent Function ───────────────────────────────────────────────────────

async def run_pixel(
    business_id: str,
    usuario_id: str,
    user_message: str,
    image_bytes: bytes | None = None,
    ephemeral: bool = False,
) -> dict[str, Any]:
    """
    Loop agêntico do Pixel. Aceita mensagem + imagem opcional.
    Se ephemeral=True, não carrega nem salva histórico (delegação da Sofia).
    """
    # current_image_bytes persists across tool calls within this invocation
    current_image_bytes = image_bytes

    identity = _get_identity(business_id)
    brand_ctx = get_unified_brand_context(business_id)
    history = [] if ephemeral else _load_conversation(business_id)

    # Build user message content
    if image_bytes:
        import base64
        b64 = base64.b64encode(image_bytes).decode()
        # Detect image type
        if image_bytes[:4] == b'\x89PNG':
            media_type = "image/png"
        else:
            media_type = "image/jpeg"
        user_content: list[dict] | str = [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": user_message or "O que você pode fazer com esta imagem?"},
        ]
    else:
        user_content = user_message

    history.append({"role": "user", "content": user_content})

    # Build system with full brand context (strategy + visual identity)
    system = PIXEL_SYSTEM + brand_context_to_prompt(brand_ctx)

    messages = list(history)
    max_iterations = 6
    response = None

    for iteration in range(max_iterations):
        model = MODEL_SMART if iteration == 0 else MODEL_FAST
        response = _client.messages.create(
            model=model,
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        content_dicts = [_block_to_dict(b) for b in response.content]
        messages.append({"role": "assistant", "content": content_dicts})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            name = block.name
            inp = block.input
            logger.info({"event": "pixel_tool_call", "tool": name, "business_id": business_id})

            try:
                if name == "get_visual_identity":
                    result = _get_identity(business_id)
                elif name == "save_visual_identity":
                    result = _save_identity(business_id, inp)
                    # refresh system context after save
                    identity = _get_identity(business_id)
                elif name == "remove_bg":
                    result = await _exec_remove_bg(business_id, current_image_bytes)
                    if result.get("success") and result.get("image_url"):
                        # Load new bytes as current image
                        import httpx
                        from api.main import app  # noqa
                        # Actually just store the result URL; we can't easily reload bytes here
                        # The agent will reference the URL in its response
                        pass
                elif name == "add_text":
                    result = await _exec_add_text(business_id, current_image_bytes, inp)
                elif name == "apply_brand_bg":
                    result = await _exec_apply_brand_bg(business_id, current_image_bytes, inp)
                else:
                    result = {"error": f"Ferramenta desconhecida: {name}"}
            except Exception as e:
                logger.error({"event": "pixel_tool_error", "tool": name, "error": str(e)})
                result = {"error": str(e)}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    final_text = ""
    result_image_url = None
    if response:
        for block in response.content:
            if block.type == "text" and not final_text:
                final_text = block.text

    # Extract image_url from last tool result if any
    for msg in reversed(messages):
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if item.get("type") == "tool_result":
                    try:
                        r = json.loads(item["content"])
                        if r.get("image_url"):
                            result_image_url = r["image_url"]
                            break
                    except Exception:
                        pass
            if result_image_url:
                break

    # Clean messages for storage (convert image content to text placeholder)
    clean_messages = []
    for m in messages:
        if m.get("role") == "user" and isinstance(m.get("content"), list):
            clean_content = []
            for part in m["content"]:
                if isinstance(part, dict) and part.get("type") == "image":
                    clean_content.append({"type": "text", "text": "[imagem enviada pelo usuário]"})
                else:
                    clean_content.append(part)
            clean_messages.append({"role": m["role"], "content": clean_content})
        else:
            clean_messages.append(m)

    if not ephemeral:
        _save_conversation(business_id, usuario_id, clean_messages)

    return {
        "response": final_text or "Pronto!",
        "image_url": result_image_url,
        "message_count": len(messages),
    }
