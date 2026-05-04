# Arquitetura dos Agentes de IA — Assistente Multimídia Social

Este documento descreve em detalhes os agentes inteligentes do sistema, suas responsabilidades, ferramentas (tools) que cada um expõe, como se comunicam entre si e como uma tarefa é executada de ponta a ponta.

---

## 1. Visão geral

O sistema é uma **agência de IA hierárquica**. Existe uma diretora criativa (Sofia) que conversa com o usuário, decide o que fazer e delega para três especialistas. Cada agente é um **loop agêntico** que usa o `tool_use` da Anthropic API: o Claude decide qual ferramenta chamar, o backend executa, devolve o resultado, e o Claude continua até produzir uma resposta final.

```
                       ┌────────────────────┐
                       │      Usuário       │
                       │ (Frontend / API)   │
                       └─────────┬──────────┘
                                 │
                                 ▼
                       ┌────────────────────┐
                       │  Sofia (Agency)    │ ← Diretora Criativa
                       │  Brand Manager     │   (orquestra a equipe)
                       └─────────┬──────────┘
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
         ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
         │ Mara         │ │  Pixel      │ │  Luna        │
         │ Social Media │ │  Designer   │ │  Google Ads  │
         └──────┬───────┘ └──────┬──────┘ └──────────────┘
                │                │
                ▼                ▼
         ┌──────────────┐ ┌──────────────┐
         │ Orchestrator │ │ Image Engine │
         │  (pipeline)  │ │  (Pillow)    │
         └──────┬───────┘ └──────────────┘
                │
       ┌────────┴───────────────┐
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│ Script Eng.  │         │ Image Engine │
│ Claude Haiku │         │ Gemini Flash │
└──────────────┘         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  Storage     │
                         │  (local/R2)  │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │  Publisher   │
                         │ Meta Graph   │
                         └──────────────┘
```

Todos os agentes **compartilham o mesmo modelo** (`claude-haiku-4-5-20251001`) para reduzir custo, e todos consomem o mesmo **Brand Context unificado** antes de cada execução, garantindo coerência entre as decisões.

---

## 2. Brand Context — o "DNA da marca"

Antes de o agente raciocinar, o backend monta um pacote único com tudo que se sabe da marca. Esse pacote vai para o `system prompt` do Claude.

**Origem:** `apps/backend/src/engines/brand_context.py`

**Função `get_unified_brand_context(business_id)`** consulta três tabelas:

| Tabela | Conteúdo |
|---|---|
| `businesses` | Nome, tipo de negócio, `brand_context` JSON (inclui análise do Instagram) |
| `brand_strategy` | Tom de voz, pilares, personas, concorrentes, frequência, objetivos |
| `visual_identity` | Cores hex, fontes, descrição de estilo, logo, referências |

**Função `brand_context_to_prompt(ctx)`** serializa tudo em um bloco `═══ CONTEXTO COMPLETO DA MARCA ═══` que é concatenado ao system prompt de cada agente, incluindo a sub-seção `── Estilo do Instagram ──` quando o perfil já foi analisado.

> **Por quê isso importa**: a Sofia, a Mara, o Pixel e a Luna recebem o mesmo "briefing" toda vez que rodam. Nada de cada agente perguntar de novo o que a empresa faz.

---

## 3. Sofia — Diretora Criativa / Brand Manager

**Arquivo:** `apps/backend/src/engines/agency/sofia_agent.py`
**Endpoint:** `POST /api/v1/agency/chat`
**Tabela de histórico:** `agency_conversations`
**Função principal:** `run_sofia(business_id, usuario_id, user_message, image_bytes=None)`

### Persona
> "Diretora criativa com passagem por W3haus, Africa e David SP."

É a única que conversa com o usuário. Coordena, decide e delega. Pode receber **imagem** junto da mensagem (multimodal).

### Regras absolutas (do system prompt)
1. **Ação primeiro** — quando pedem conteúdo, cria na hora com `create_content_direct`.
2. Máximo 1 pergunta por resposta.
3. Respostas curtas (2-4 parágrafos), sem listas longas.
4. Nunca pergunta o que já está no Brand Context.
5. Tom de consultora sênior, não de chatbot.

### Tools (13 no total)

| Tool | O que faz |
|---|---|
| `get_brand_profile` | Retorna o Brand Context completo |
| `update_brand_strategy` | Atualiza pilares, tom, objetivos, personas, concorrentes |
| `update_visual_identity` | Atualiza cores, fontes, estilo |
| `update_business_profile` | Atualiza descrição, serviços, público, localização |
| `create_content_direct` | **Atalho rápido**: cria post/story/reel/carrossel via orchestrator (bypassa Mara) |
| `delegate_to_mara` | Delega tarefa complexa para Mara (análise, calendário) |
| `delegate_to_pixel` | Delega tarefa visual para Pixel |
| `delegate_to_luna` | Delega análise de tráfego pago para Luna |
| `get_content_overview` | Estatísticas de drafts (pendentes, aprovados, publicados) |
| `list_pending_drafts` | Lista drafts aguardando aprovação |
| `check_readiness` | Score 0-100% do quanto o perfil está completo |
| `analyze_client_url` | Faz scrape do site/IG/LinkedIn e auto-merge no perfil |
| `analyze_instagram_style` | Roda o Instagram Analyzer para extrair estilo do feed |

### Como ela delega
A Sofia chama internamente `run_agent` (Mara), `run_pixel` ou `run_luna` em **modo `ephemeral=True`**: o agente filho **não carrega nem salva histórico próprio**. Isso evita poluir o histórico do especialista quando ele é chamado pela Sofia. O resultado volta como `tool_result` para o loop dela.

### Loop agêntico
```
1. Carrega histórico da agency_conversations
2. Monta system = SOFIA_SYSTEM + brand_context_to_prompt(ctx)
3. Anexa user_message (com imagem se houver)
4. Roda até 10 iterações:
     a. Claude responde (texto OU tool_use)
     b. Se tool_use → executa tool, devolve resultado, repete
     c. Caso contrário → encerra
5. Compacta o histórico (remove imagens base64, trunca tool_results) e salva
```

### Atalho `create_content_direct`
Para conteúdo simples, a Sofia bypassa a Mara e chama o `orchestrator.generate_content` diretamente — economiza ~3 chamadas Claude e ~75% do custo da pipeline. Ela passa `uploaded_image_url` quando o usuário enviou uma foto e quer usá-la no post.

---

## 4. Mara — Head de Social Media

**Arquivo:** `apps/backend/src/engines/agent/social_media_agent.py`
**Endpoint:** `POST /api/v1/agent/chat`
**Tabela de histórico:** `agent_conversations`
**Função principal:** `run_agent(business_id, usuario_id, user_message, ephemeral=False)`

### Persona
> "Head de Social Media, 10 anos liderando estratégia para Reserva, Amaro e Liv Up."

Especialista em estratégia de conteúdo, calendário editorial e análise de performance. É chamada quando a tarefa é mais complexa que "cria um post" — ex.: "monta minha próxima semana", "como meus carrosséis estão performando?".

### Tools (10 no total)

| Tool | O que faz |
|---|---|
| `generate_content` | Cria 1 conteúdo via orchestrator (post / story / reel / carrossel) |
| `generate_batch_content` | Cria até 7 conteúdos em paralelo (`asyncio.gather`) |
| `list_pending_drafts` | Lista drafts pendentes |
| `approve_draft` | Aprova um draft pelo ID |
| `schedule_draft` | Aprova + agenda em data/hora ISO |
| `get_post_history` | Histórico de posts publicados |
| `analyze_performance` | Taxa de aprovação, formatos top, melhores horários |
| `suggest_editorial_calendar` | Calendário editorial (até 30 dias) baseado em pilares |
| `get_business_info` | Business + estratégia atuais |
| `update_brand_strategy` | Atualiza pilares, tom, frequência, objetivos |

### Loop e modelo
- Até **8 iterações**.
- Modelo: Haiku 4.5 em todas as iterações (constantes `MODEL_SMART = MODEL_FAST`).
- `ephemeral=True` quando chamada pela Sofia → não persiste histórico.

### Como ela cria conteúdo
A Mara nunca chama o Claude para gerar a imagem diretamente. Ela invoca `orchestrator.generate_content`, que faz:
1. **Script** (Claude Haiku) → caption, hashtags, prompt visual em inglês
2. **Imagem** (Gemini Flash) → bytes da imagem
3. **Storage** (`upload_image`) → URL pública
4. **DB** → insere em `content_drafts` com `status='pending_approval'`

Para carrossel, gera 1 imagem por slide sequencialmente (evita rate limit do Gemini).

---

## 5. Pixel — Diretor de Arte / Designer Visual

**Arquivo:** `apps/backend/src/engines/designer/pixel_agent.py`
**Endpoint:** `POST /api/v1/designer/chat`
**Tabela de histórico:** `designer_conversations`
**Função principal:** `run_pixel(business_id, usuario_id, user_message, image_bytes=None, ephemeral=False)`

### Persona
> "Diretor de Arte com 12 anos em branding (Nubank, iFood, Natura)."

Especialista em **identidade visual** e **edição de imagens**. Aceita imagem como input (multimodal) — o usuário pode mandar uma foto e pedir "remove o fundo, aplica nossa cor primária e escreve 'Promoção'".

### Tools (5 no total)

| Tool | O que faz |
|---|---|
| `get_visual_identity` | Lê cores/fontes salvas |
| `save_visual_identity` | Salva paleta, fontes, estilo, contexto extra |
| `remove_bg` | Remove fundo da imagem enviada (usa biblioteca `rembg`) |
| `add_text` | Adiciona texto sobre a imagem (Pillow + DejaVu/Liberation) |
| `apply_brand_bg` | Aplica cor de fundo da marca em imagem com fundo transparente |

### Engine de composição
Tudo em `apps/backend/src/engines/image_engine/composer.py` (Pillow puro):
- `remove_background(bytes)` — `rembg` retorna PNG transparente
- `add_text_overlay(...)` — faixa semi-transparente + texto centralizado
- `apply_brand_background(...)` — cola a imagem sem fundo sobre cor sólida

### Estado entre tools
A imagem original (`image_bytes`) fica em escopo na função `run_pixel`. Cada tool processa a partir dela. O resultado é **sempre publicado** no storage (`upload_image`) e a URL retorna para o Claude. A imagem "atual" que o agente mostra na resposta vem do **último tool_result com `image_url`**.

### Loop
- Até 6 iterações (mais curto que os outros — operações de edição são pontuais).
- Quando salva no histórico, substitui blocos `image` por `[imagem enviada pelo usuário]` (economia de tokens).

---

## 6. Luna — Head de Performance / Google Ads

**Arquivo:** `apps/backend/src/engines/ads_agent/luna_agent.py`
**Endpoint:** `POST /api/v1/ads/chat`
**Tabela de histórico:** `luna_conversations`
**Função principal:** `run_luna(business_id, usuario_id, user_message, ephemeral=False)`

### Persona
> "Head de Performance, 8 anos gerenciando +R$5M em budget (Magalu, Dafiti, Insider)."

Estrategista de tráfego pago. Não ensina conceitos — diagnostica e age.

### Tools (10 no total)

| Tool | O que faz |
|---|---|
| `get_ads_account` | Verifica se há conta Google Ads conectada |
| `get_account_overview` | Métricas dos últimos 30 dias (impressões, cliques, custo, CTR, conversões) |
| `list_campaigns` | Lista campanhas com performance |
| `pause_campaign` / `enable_campaign` | Pausa/ativa campanha |
| `get_keywords` | Keywords de uma campanha |
| `suggest_keywords` | Sugere 15 keywords (Claude Sonnet — única tool que ainda usa Sonnet) |
| `update_budget` | Altera orçamento diário |
| `analyze_performance` | Diagnóstico: top spend, baixo CTR, ativas vs pausadas |
| `get_business_info` | Business + tipo |

### Modo "real" vs "mock"
A função `_try_real_or_mock` decide:
- Se a `google_ads_accounts` tem `refresh_token` → chama Google Ads API real.
- Se não → retorna dados mock com `note: "[MOCK]"`. A Luna avisa **uma vez** que são dados de demonstração.

Isso permite testar todo o fluxo sem precisar de conta Google Ads conectada.

---

## 7. Comunicação entre agentes

### 7.1. Modelo: Sofia delega via chamadas Python diretas

A Sofia **não usa fila nem HTTP** para falar com Mara/Pixel/Luna. Ela importa e chama as funções `run_*` no mesmo processo:

```python
# em sofia_agent.py
async def _exec_delegate_to_mara(business_id, usuario_id, task):
    from src.engines.agent.social_media_agent import run_agent
    result = await run_agent(business_id, usuario_id, user_message=task, ephemeral=True)
    return {"agent": "mara", "success": True, "response": result["response"]}
```

A flag `ephemeral=True` é fundamental:
- O agente filho **não carrega** o histórico próprio (usa só o `task` recebido).
- O agente filho **não salva** mensagens (não polui sua tabela de conversas).
- A resposta volta como string para o `tool_result` da Sofia.

### 7.2. Resumo dos canais

| De → Para | Mecanismo | Efeito colateral |
|---|---|---|
| Frontend → Sofia | HTTP POST `/api/v1/agency/chat` | Salva em `agency_conversations` |
| Frontend → Mara/Pixel/Luna | HTTP POST direto no endpoint do agente | Salva no histórico próprio |
| Sofia → Mara | `run_agent(...,ephemeral=True)` em-processo | Sem persistência |
| Sofia → Pixel | `run_pixel(...,ephemeral=True)` em-processo | Sem persistência |
| Sofia → Luna | `run_luna(...,ephemeral=True)` em-processo | Sem persistência |
| Agentes → Orchestrator | `generate_content(...)` em-processo | Cria `content_drafts` |
| Orchestrator → Script Engine | `generate_post_script(...)` (Claude) | — |
| Orchestrator → Image Engine | `generate_image_gemini(...)` | — |
| Orchestrator → Storage | `upload_image(bytes, format)` | URL pública |

> Hoje toda comunicação é **síncrona, em-processo**. O CLAUDE.md menciona Redis/BullMQ na visão futura, mas o MVP atual roda tudo no mesmo monolito FastAPI.

---

## 8. Fluxos completos

### 8.1. "Sofia, cria um post promovendo nossa Black Friday"

```
1. Frontend → POST /api/v1/agency/chat
   { business_id, message: "cria post Black Friday 30% off" }

2. run_sofia():
   - get_unified_brand_context(business_id)  → carrega marca
   - history = _load_conversation(business_id)
   - system = SOFIA_SYSTEM + brand_context_to_prompt(ctx)
   - Claude(messages, tools) → tool_use: create_content_direct
       { objective: "Black Friday 30% off", format: "post", tone: "urgente" }

3. _exec_create_content_direct():
   - orchestrator.generate_content(...)
       a. claude_client.generate_post_script() → caption + visual_description (EN)
       b. imagen_client.generate_image_gemini() → bytes da imagem
       c. storage.upload_image() → URL
       d. INSERT INTO content_drafts (status='pending_approval')
   - retorna { draft_id, caption, image_url, status }

4. Sofia recebe tool_result e gera texto final em PT-BR:
   "Pronto! Post de Black Friday criado e está em Revisar & Aprovar."

5. _save_conversation(business_id, ...) → atualiza agency_conversations.

6. Frontend recebe { response, steps: [{agent: "mara", action, status}] }
   e mostra no chat + redireciona para tela de aprovação.
```

### 8.2. "Sofia, analisa nossa performance da última semana"

```
1. Sofia identifica como tarefa complexa de análise
2. tool_use: delegate_to_mara { task: "Analise performance dos últimos 7 dias..." }
3. _exec_delegate_to_mara → run_agent(..., ephemeral=True)
   - Mara: tool_use: analyze_performance → SQL agregado em content_drafts
   - Mara devolve texto: "Seu CTR de carrosséis está 2,3x acima dos posts..."
4. Sofia recebe a string como tool_result
5. Sofia consolida e devolve ao usuário
```

### 8.3. "Pixel, remove o fundo dessa foto e coloca nossa cor primária"

```
1. Frontend → POST /api/v1/designer/chat (multipart com imagem)
2. run_pixel():
   - image_bytes recebido em escopo
   - tool_use: remove_bg → composer.remove_background(image_bytes) → PNG transp.
   - upload_image() → URL_1
   - tool_use: apply_brand_bg → composer.apply_brand_background(...) → JPEG
   - upload_image() → URL_2
3. Resposta: "Pronto. Fundo removido e aplicada a cor #FF6B35 da identidade."
4. URL_2 vem em response.image_url para o frontend exibir
```

### 8.4. Geração de carrossel (caminho mais elaborado do Orchestrator)

```
generate_content(format="carrossel", slide_count=5):
  script = generate_post_script(format="carrossel")
    → Claude retorna: { caption, hashtags, slides:[{visual_description, text_overlay}, ...] }
  for slide in script["slides"]:                    # sequencial (rate limit)
      bytes = generate_image_gemini(slide.visual_description, brand_context=ctx)
      url = upload_image(bytes, "post")
      urls.append(url)
  INSERT content_drafts (image_urls=JSON(urls), visual_description=JSON(slides), status='pending_approval')
```

---

## 9. Tabelas de persistência relacionadas aos agentes

| Tabela | Dono | Função |
|---|---|---|
| `agency_conversations` | Sofia | Histórico do chat com a Sofia |
| `agent_conversations` | Mara | Histórico do chat com a Mara |
| `designer_conversations` | Pixel | Histórico do chat com o Pixel |
| `luna_conversations` | Luna | Histórico do chat com a Luna |
| `businesses` | — | Negócio + `brand_context` JSON (inclui `instagram_style`) |
| `brand_strategy` | — | Pilares, tom, personas, frequência, concorrentes |
| `visual_identity` | — | Cores hex, fontes, estilo, logo |
| `content_drafts` | Orchestrator | Posts gerados aguardando aprovação |
| `scheduled_posts` | Orchestrator/Mara | Drafts agendados |
| `google_ads_accounts` | Luna | Refresh tokens da Google Ads API |

Todas as tabelas de conversa guardam apenas as **últimas 20 mensagens** (`messages[-20:]`) e compactam blocos pesados (imagens base64, tool_results gigantes).

---

## 10. Engines auxiliares (sub-componentes que os agentes usam)

### Script Engine
`src/engines/script_engine/claude_client.py` — `generate_post_script(format)` despacha para um dos três templates (`POST_PROMPT`, `STORY_PROMPT`, `CAROUSEL_PROMPT`). Cada template **exige caption em PT-BR e prompt de imagem em inglês** (modelos de imagem geram melhor com EN). Injeta `brand_strategy.visual_identity` (cores hex, descrição de estilo) e `instagram_style` no prompt.

### Image Engine
- `imagen_client.py` — wrapper do **Gemini 3.1 Flash** para imagem (default).
- `dalle_client.py` — fallback para DALL-E 3 (apenas se `OPENAI_API_KEY` configurado).
- `composer.py` — Pillow + rembg para edição (tools do Pixel).
- `storage.py` — `upload_image(bytes, format)` salva localmente em `apps/backend/assets/...` ou em R2 (em produção).

### Intelligence
- `instagram_analyzer.py` — chama Meta Graph (`fetch_recent_posts`), pega 12 posts e pede ao Claude para extrair `writing_style`, `visual_style`, `content_patterns` e um `image_prompt_guide` em inglês. Persiste em `businesses.brand_context.instagram_style`.
- `web_scraper.py` — `analyze_website(url)` faz scrape do site/IG/LinkedIn enviado pela Sofia e devolve campos para auto-merge no perfil.

### Publisher
- `publisher/instagram.py` — Meta Graph API: `publish_image_post`, `publish_carousel_post`, `fetch_recent_posts`.
- `publisher/token_manager.py` — Fernet para criptografar/descriptografar tokens.
- `publisher/linkedin.py`, `tiktok.py` — esqueletos (não são usados pelo MVP).

---

## 11. Padrões compartilhados por todos os agentes

Todos os 4 agentes seguem **o mesmo molde estrutural** — útil ao adicionar um novo agente:

1. **Constantes**: `MODEL_SMART`, `MODEL_FAST` (ambos Haiku), `<NOME>_SYSTEM` (persona).
2. **Lista `TOOLS`**: schema JSON Schema das ferramentas.
3. **Executors `_exec_<tool_name>`**: implementação da tool.
4. **`_load_conversation` / `_save_conversation`**: persistência da tabela própria.
5. **`_block_to_dict`**: serializa blocos `text` e `tool_use`.
6. **`run_<nome>(business_id, usuario_id, user_message, ephemeral=False)`**: o loop agêntico — carrega contexto, monta system, itera com `tool_use` até `max_iterations`, salva histórico (se não-efêmero) e retorna `{ response, message_count }` (mais campos opcionais).

### Limites de iteração por agente
| Agente | max_iterations |
|---|---|
| Sofia | 10 |
| Mara | 8 |
| Luna | 8 |
| Pixel | 6 |

### Persistência: invariantes
- Histórico é **truncado nas últimas 20 mensagens** antes de salvar.
- A primeira mensagem precisa ser **role=user com conteúdo válido** — a API do Claude rejeita histórico que comece com `tool_result` ou `assistant`.
- `tool_result` longos são truncados a 200 chars na hora de salvar (a Sofia faz isso explicitamente em `_compact_messages`).

---

## 12. Como adicionar um novo agente (receita)

1. Criar `src/engines/<area>/<nome>_agent.py` copiando a estrutura da Mara (mais simples sem multimodal) ou do Pixel (com multimodal).
2. Definir persona em `<NOME>_SYSTEM` no estilo "consultora sênior, executa, máximo 1 pergunta".
3. Listar tools em `TOOLS` (JSON Schema).
4. Implementar `_exec_*` para cada tool.
5. Criar tabela `<nome>_conversations` (mesma estrutura das existentes — ver `db/schema.py`).
6. Criar `api/<nome>/router.py` com `POST /chat`, `GET /history/{business_id}`, `DELETE /history/{business_id}`.
7. Registrar `app.include_router(<nome>_router)` em `api/main.py`.
8. Adicionar `delegate_to_<nome>` como tool da Sofia + `_exec_delegate_to_<nome>` chamando `run_<nome>(..., ephemeral=True)`.
9. Adicionar página no frontend (padrão `*Page.tsx`) consumindo o endpoint.

---

## 13. Decisões de arquitetura que importam

- **Haiku para tudo**: economia de ~75% vs Sonnet. A única exceção é `Luna.suggest_keywords` (Sonnet, ainda).
- **Brand Context único e injetado em system prompt**: agentes nunca repetem perguntas que o perfil já responde.
- **Delegação em-processo (não fila)**: simplicidade do MVP. Trocar para Redis/BullMQ depois requer apenas que `_exec_delegate_to_*` enfileire e aguarde o resultado.
- **Aprovação obrigatória**: nada é publicado sem o usuário aprovar (`status='pending_approval'` é o estado inicial sempre).
- **Imagens sempre via storage próprio**: nunca passar URL temporária do Gemini/DALL-E direto para o Instagram.
- **Modo `ephemeral`**: permite que a Sofia delegue sem poluir histórico do agente filho — crítico para boa UX no chat individual de cada especialista.
