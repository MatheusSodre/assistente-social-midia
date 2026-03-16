# CLAUDE.md — Assistente Multimídia Social

Você é o engenheiro principal deste projeto. Seu papel é construir, evoluir e manter o **Assistente Multimídia Social** — uma plataforma SaaS que automatiza a gestão de redes sociais para empresas e influenciadores usando IA generativa.

---

## 🧠 Contexto do Projeto

Este sistema permite que qualquer negócio (e-commerce, clínicas, lojas, influenciadores) conecte sua conta e receba:
- Criação automática de conteúdo (imagens, vídeos, textos) via IA
- Agendamento inteligente de publicações
- Fluxo de aprovação antes de postar
- API pública para integrações externas

**MVP atual:** Instagram (posts + stories) com geração de imagem via IA e aprovação pelo usuário.

---

## 🏗️ Arquitetura do Sistema

```
[API Gateway - FastAPI]
        ↓
[Orquestrador - orchestrator-engine]
    ↙       ↓        ↓        ↘
[script] [image] [video]  [publisher]
engine   engine  engine     engine
    ↓       ↓        ↓        ↓
[Claude] [DALL-E] [Runway] [Meta API]
  API    /Flux             [TikTok API]
```

### Módulos (apps/)

| Módulo | Linguagem | Responsabilidade |
|--------|-----------|-----------------|
| `orchestrator` | Python | Motor central, agenda, gerencia fluxo |
| `script-engine` | Python | Gera roteiros, captions, hashtags via Claude |
| `image-engine` | Python | Gera imagens para posts/stories via DALL-E ou Flux |
| `video-engine` | Python | Gera Reels curtos (Runway + FFmpeg + ElevenLabs) |
| `publisher` | TypeScript | Posta no Instagram via Meta Graph API |
| `api-gateway` | TypeScript | REST API pública, auth, webhook |
| `dashboard` | TypeScript | Frontend de aprovação e calendário editorial |

---

## 📁 Estrutura de Pastas

```
assistente-social-midia/
├── apps/
│   ├── orchestrator/          # Python - motor central
│   │   ├── main.py
│   │   ├── scheduler.py       # APScheduler para agendamentos
│   │   ├── queue.py           # Fila de tarefas (Redis/BullMQ)
│   │   └── models/
│   ├── script-engine/         # Python - geração de conteúdo
│   │   ├── main.py
│   │   ├── claude_client.py
│   │   └── prompts/           # Templates de prompt por nicho
│   ├── image-engine/          # Python - geração de imagens
│   │   ├── main.py
│   │   ├── dalle_client.py
│   │   └── flux_client.py
│   ├── video-engine/          # Python - geração de vídeos
│   │   ├── main.py
│   │   └── ffmpeg_utils.py
│   ├── publisher/             # TypeScript - publicação
│   │   ├── src/
│   │   │   ├── instagram.ts   # Meta Graph API
│   │   │   └── scheduler.ts
│   │   └── package.json
│   └── api-gateway/           # TypeScript - API pública
│       ├── src/
│       │   ├── routes/
│       │   ├── middleware/
│       │   └── index.ts
│       └── package.json
├── whatsapp/                  # Notificações via WhatsApp
├── docs/                      # Documentação técnica
├── .env.example
├── docker-compose.yml
└── CLAUDE.md
```

---

## ⚙️ Stack Técnica

### Backend Python
- **FastAPI** — APIs dos engines
- **APScheduler** — agendamento de tarefas
- **Celery + Redis** — fila de processamento assíncrono
- **SQLAlchemy + PostgreSQL** — persistência
- **Pydantic** — validação de dados

### Backend TypeScript
- **Node.js + Express** ou **Fastify** — API Gateway e Publisher
- **Prisma** — ORM para PostgreSQL
- **BullMQ** — fila de jobs

### IA e Mídia
- **Claude API (claude-sonnet-4-20250514)** — geração de roteiros/textos
- **DALL-E 3 ou Flux Pro (Replicate)** — geração de imagens
- **Runway ML** — geração de vídeos curtos
- **ElevenLabs** — narração TTS para vídeos
- **FFmpeg** — edição/montagem de vídeo

### Integrações
- **Meta Graph API** — publicação no Instagram
- **WhatsApp Business API** — notificações de aprovação
- **Cloudflare R2 / AWS S3** — storage de mídia

---

## 🔑 Variáveis de Ambiente (.env)

```env
# Anthropic
ANTHROPIC_API_KEY=

# Imagem
OPENAI_API_KEY=
REPLICATE_API_TOKEN=

# Vídeo
RUNWAY_API_KEY=
ELEVENLABS_API_KEY=

# Instagram
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/assistente_social

# Redis
REDIS_URL=redis://localhost:6379

# Storage
R2_BUCKET=
R2_ACCESS_KEY=
R2_SECRET_KEY=

# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
```

---

## 🔄 Fluxo Principal do MVP

```
1. Cliente envia brief via API
   POST /api/v1/content/generate
   { "business_type": "dentista", "objetivo": "promoção limpeza", "formato": "post" }

2. Orchestrator recebe e dispara:
   → script-engine: gera caption + hashtags + descrição visual
   → image-engine: gera imagem baseada na descrição visual
   → monta ContentDraft com tudo junto

3. Sistema notifica usuário para aprovação
   → WhatsApp: "Seu post está pronto! Clique para aprovar."
   → Dashboard: preview com botões Aprovar / Editar / Rejeitar

4. Usuário aprova → publisher agenda/posta no Instagram
   → Meta Graph API: POST /media + /media_publish

5. Orchestrator registra no histórico e atualiza calendário
```

---

## 📡 API Pública (MVP)

```
POST   /api/v1/auth/register          # Criar conta
POST   /api/v1/auth/login             # Login
POST   /api/v1/accounts/connect       # Conectar Instagram (OAuth)
POST   /api/v1/content/generate       # Gerar conteúdo
GET    /api/v1/content/:id/preview    # Ver preview
POST   /api/v1/content/:id/approve    # Aprovar conteúdo
POST   /api/v1/content/:id/reject     # Rejeitar conteúdo
GET    /api/v1/schedule/calendar      # Calendário editorial
POST   /api/v1/schedule/post          # Agendar publicação
GET    /api/v1/posts/history          # Histórico de posts
```

---

## 🗄️ Modelos de Dados (MVP)

### Business (Cliente)
```python
class Business(Base):
    id: UUID
    name: str
    type: str  # dentista, ecommerce, automovel, etc
    instagram_account_id: str
    instagram_access_token: str  # encrypted
    brand_context: JSON  # cores, tom de voz, logo
    created_at: datetime
```

### ContentDraft (Rascunho de Conteúdo)
```python
class ContentDraft(Base):
    id: UUID
    business_id: UUID
    format: str  # post | story | reel
    caption: str
    hashtags: list[str]
    image_url: str
    video_url: str | None
    status: str  # pending_approval | approved | rejected | published
    scheduled_for: datetime | None
    created_at: datetime
```

### ScheduledPost (Agendamento)
```python
class ScheduledPost(Base):
    id: UUID
    content_draft_id: UUID
    platform: str  # instagram
    scheduled_for: datetime
    posted_at: datetime | None
    instagram_media_id: str | None
    status: str  # scheduled | published | failed
```

---

## 🤖 Prompts Padrão (script-engine)

### Geração de Post
```python
SYSTEM_PROMPT = """
Você é um especialista em marketing digital e copywriting para redes sociais.
Sempre gere conteúdo em português brasileiro.
Retorne APENAS JSON válido, sem markdown.
"""

USER_PROMPT = """
Crie um post para Instagram para o seguinte negócio:

Tipo de negócio: {business_type}
Nome da empresa: {business_name}
Objetivo do post: {objective}
Tom de voz: {tone}  # profissional | descontraído | urgente | educativo
Público-alvo: {audience}

Retorne exatamente neste formato JSON:
{
  "caption": "texto do post (máx 2200 chars)",
  "hashtags": ["lista", "de", "hashtags", "relevantes"],
  "visual_description": "descrição detalhada da imagem ideal para este post",
  "call_to_action": "texto do CTA",
  "best_posting_time": "horário sugerido HH:MM"
}
"""
```

### Geração de Story
```python
STORY_PROMPT = """
Crie um story para Instagram:

Tipo de negócio: {business_type}
Objetivo: {objective}

Retorne JSON:
{
  "text_overlay": "texto principal (máx 30 palavras)",
  "visual_description": "descrição detalhada do visual do story 9:16",
  "sticker_suggestion": "enquete | countdown | slider | pergunta",
  "sticker_text": "texto para o sticker"
}
"""
```

---

## 🖼️ Geração de Imagem (image-engine)

### Formatos por tipo
```python
IMAGE_FORMATS = {
    "post": {"width": 1080, "height": 1080, "ratio": "1:1"},
    "story": {"width": 1080, "height": 1920, "ratio": "9:16"},
    "landscape": {"width": 1080, "height": 566, "ratio": "1.91:1"},
}

# Prompt base para DALL-E 3
IMAGE_SYSTEM = """
Professional marketing photo for Brazilian business.
High quality, clean, modern aesthetic.
No text overlays in the image.
Style: commercial photography, well-lit, sharp.
"""
```

---

## ✅ Regras de Desenvolvimento

### Python
- Use **type hints** em tudo
- **Pydantic** para todos os schemas de entrada/saída
- **async/await** para chamadas de API externas
- Trate erros com `try/except` explícito e logue com contexto
- Nunca commite credenciais — sempre use variáveis de ambiente

### TypeScript
- **Strict mode** ligado no tsconfig
- Use **zod** para validação de dados nas rotas
- Funções assíncronas com `async/await`, nunca callbacks
- Erros devem retornar `{ error: string, code: string }`

### Geral
- Cada engine roda de forma **independente** (pode ser escalado separadamente)
- Comunicação entre engines via **HTTP interno** ou **fila Redis**
- Toda mídia gerada vai para **R2/S3** antes de ir ao Instagram
- Logs estruturados em JSON (para fácil parsing)

---

## 🚀 Ordem de Build do MVP

```
Semana 1: Fundação
  ✅ Setup do repositório e docker-compose
  ✅ PostgreSQL + Redis + estrutura de pastas
  ✅ API Gateway base com auth JWT

Semana 2: Motor de Conteúdo
  → script-engine: integração Claude API + prompts por nicho
  → image-engine: integração DALL-E 3 + upload R2

Semana 3: Publicação
  → publisher: Meta Graph API + OAuth Instagram
  → Fluxo de aprovação via WhatsApp

Semana 4: Orquestração
  → orchestrator: agendador + calendário editorial
  → Dashboard simples de aprovação (HTML/React)

Semana 5: Testes e Ajustes
  → Teste com cliente piloto real
  → Monitoramento de erros
  → Documentação da API
```

---

## 🐛 Debugging Comum

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Testar geração de conteúdo direto
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{"business_type": "dentista", "objective": "promoção limpeza", "format": "post"}'

# Verificar fila Redis
redis-cli LLEN content_generation_queue

# Reset de token Instagram (quando expirar)
python apps/publisher/refresh_token.py
```

---

## 📌 Decisões de Arquitetura Importantes

1. **Aprovação sempre obrigatória no MVP** — nunca poste automaticamente sem aprovação explícita do usuário
2. **Um `business_id` por conta Instagram** — não misture conteúdo de clientes diferentes
3. **Imagens geradas ficam em storage próprio** — nunca use URLs temporárias da DALL-E diretamente no Instagram
4. **Tokens do Instagram criptografados no banco** — use `cryptography` (Fernet) para encrypt/decrypt
5. **Rate limits da Meta API** — máximo 25 posts por dia por conta, respeite os limites
6. **Fallback de imagem** — se DALL-E falhar, tente Flux (Replicate) antes de retornar erro

---

## 🔗 Documentação de Referência

- Meta Graph API (Instagram): https://developers.facebook.com/docs/instagram-api
- Anthropic Claude API: https://docs.anthropic.com
- DALL-E 3: https://platform.openai.com/docs/guides/images
- Replicate (Flux): https://replicate.com/docs
- Runway ML: https://docs.runwayml.com
- ElevenLabs TTS: https://docs.elevenlabs.io