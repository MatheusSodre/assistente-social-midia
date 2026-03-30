"""
PDF Extractor — Extrai texto de PDFs e analisa com Claude para extrair dados do negócio.
"""
import json
import logging
import re
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic()

EXTRACT_PROMPT = """Analise o conteúdo deste documento ({filename}) de um negócio e extraia informações relevantes.
Retorne APENAS JSON válido:

{{
  "description": "descrição do negócio se mencionada",
  "services": ["produtos ou serviços mencionados"],
  "target_audience": "público-alvo se mencionado",
  "differentials": "diferenciais ou proposta de valor",
  "brand_tone": "tom de comunicação detectado: profissional | descontraido | urgente | educativo | inspiracional | humoristico",
  "content_pillars": ["temas/pilares de conteúdo sugeridos"],
  "goals": ["objetivos mencionados ou sugeridos"],
  "colors": ["cores mencionadas em hex se houver"],
  "style_description": "estilo visual descrito se houver",
  "key_info": "qualquer outra informação importante sobre o negócio"
}}

Conteúdo do documento:
{content}
"""


async def extract_from_pdf(file_bytes: bytes, filename: str = "document") -> dict[str, Any]:
    """Extract text from PDF and analyze with Claude."""

    # Try pdfplumber first, fallback to simple extraction
    text = ""
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages[:20]):  # Max 20 pages
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
    except ImportError:
        # pdfplumber not installed — try PyPDF2
        try:
            import PyPDF2
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages[:20]:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
        except ImportError:
            return {"error": "Nenhuma biblioteca PDF disponível. Instale pdfplumber ou PyPDF2."}
        except Exception as e:
            return {"error": f"Erro ao ler PDF: {str(e)}"}
    except Exception as e:
        return {"error": f"Erro ao ler PDF: {str(e)}"}

    if not text or len(text.strip()) < 20:
        return {"error": "PDF não contém texto extraível (pode ser escaneado/imagem)."}

    # Limit text for Claude
    text = text[:8000]

    try:
        response = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="Você analisa documentos de negócios e extrai informações estruturadas. Retorne APENAS JSON válido.",
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(filename=filename, content=text)}],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r'^```\w*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        result = json.loads(raw)
        result["source"] = filename
        result["source_type"] = "document"
        return result
    except json.JSONDecodeError:
        return {"error": "Não foi possível interpretar o conteúdo do documento."}
    except Exception as e:
        return {"error": f"Erro na análise: {str(e)}"}
