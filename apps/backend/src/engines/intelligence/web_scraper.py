"""
Web Scraper — Analisa website/Instagram/LinkedIn de um negócio usando Claude.
Extrai informações estruturadas para o perfil do negócio.
"""
import json
import logging
import re
from typing import Any

import anthropic
import httpx

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

EXTRACT_PROMPT = """Analise o conteúdo deste website/página e extraia informações sobre o negócio.
Retorne APENAS JSON válido com esta estrutura (campos que não conseguir identificar, deixe null):

{{
  "description": "descrição resumida do negócio em 2-3 frases",
  "services": ["lista", "de", "produtos", "ou", "servicos"],
  "target_audience": "descrição do público-alvo provável",
  "differentials": "o que diferencia este negócio (proposta de valor)",
  "location": "cidade/região se mencionada",
  "brand_tone": "tom de voz detectado: profissional | descontraido | urgente | educativo | inspiracional | humoristico",
  "content_pillars": ["pilares de conteúdo sugeridos baseado no negócio"],
  "goals": ["objetivos de marketing sugeridos"],
  "colors": ["cores hex detectadas no site se houver"],
  "style_description": "descrição do estilo visual do site/marca"
}}

URL analisada: {url}
Conteúdo:
{content}
"""


def _clean_html(html: str) -> str:
    """Strip HTML tags and extract meaningful text."""
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Extract meta tags
    metas = []
    for match in re.finditer(r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE):
        metas.append(match.group(1))
    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""
    # Strip all remaining tags
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()

    # Combine
    parts = []
    if title:
        parts.append(f"Título: {title}")
    if metas:
        parts.append(f"Meta: {'; '.join(metas[:5])}")
    parts.append(text[:8000])  # Limit text length for Claude
    return "\n".join(parts)


async def analyze_website(url: str) -> dict[str, Any]:
    """Fetch a URL and analyze it with Claude to extract business intelligence."""
    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    # Detect if it's an Instagram URL
    if "instagram.com" in url:
        return await _analyze_instagram_url(url)

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; BusinessAnalyzer/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            })
            resp.raise_for_status()
            html = resp.text
    except httpx.TimeoutException:
        return {"error": f"Timeout ao acessar {url}. Verifique se o site está online."}
    except httpx.HTTPStatusError as e:
        return {"error": f"Erro HTTP {e.response.status_code} ao acessar {url}"}
    except Exception as e:
        return {"error": f"Não foi possível acessar {url}: {str(e)}"}

    content = _clean_html(html)
    if len(content) < 50:
        return {"error": "Página retornou conteúdo insuficiente para análise."}

    # Analyze with Claude
    try:
        response = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Você é um analista de marketing que extrai informações de negócios a partir de websites. Retorne APENAS JSON válido.",
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(url=url, content=content[:6000])}],
        )
        raw = response.content[0].text.strip()
        # Clean potential markdown wrapping
        if raw.startswith("```"):
            raw = re.sub(r'^```\w*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        result = json.loads(raw)
        result["source"] = url
        result["source_type"] = "website"
        return result
    except json.JSONDecodeError:
        logger.error({"event": "web_scraper_json_error", "url": url})
        return {"error": "Não foi possível interpretar o conteúdo do site."}
    except Exception as e:
        logger.error({"event": "web_scraper_error", "url": url, "error": str(e)})
        return {"error": f"Erro na análise: {str(e)}"}


async def _analyze_instagram_url(url: str) -> dict[str, Any]:
    """Analyze an Instagram profile from its URL."""
    # Extract handle from URL
    match = re.search(r'instagram\.com/([^/?#]+)', url)
    handle = match.group(1) if match else url

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(f"https://www.instagram.com/{handle}/", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html",
            })
            html = resp.text
    except Exception as e:
        return {"error": f"Não foi possível acessar o Instagram: {str(e)}"}

    # Extract meta tags (og:description usually has bio)
    metas = {}
    for match in re.finditer(r'<meta\s+(?:property|name)=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\']', html):
        metas[match.group(1)] = match.group(2)

    bio = metas.get("og:description", metas.get("description", ""))
    title = metas.get("og:title", "")

    content = f"Perfil Instagram: @{handle}\nTítulo: {title}\nBio: {bio}"

    if len(bio) < 10:
        return {
            "source": f"instagram.com/{handle}",
            "source_type": "instagram",
            "description": f"Perfil Instagram @{handle}",
            "error_note": "Não foi possível extrair dados detalhados do Instagram (perfil pode ser privado).",
        }

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Analise este perfil de Instagram e extraia informações do negócio. Retorne APENAS JSON válido.",
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(url=f"instagram.com/{handle}", content=content)}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r'^```\w*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        result = json.loads(raw)
        result["source"] = f"instagram.com/{handle}"
        result["source_type"] = "instagram"
        return result
    except Exception as e:
        return {"error": f"Erro na análise do Instagram: {str(e)}"}
