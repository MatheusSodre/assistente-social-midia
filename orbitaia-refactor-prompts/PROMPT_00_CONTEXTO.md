# PROMPT 00 — Contexto Geral

> Você é um assistente de implementação trabalhando no monorepo `assistente-social-midia`, no caminho `/home/sodre/www/orbita.ia/assistente-social-midia`. Pasta `frontend/` (React 19 + Vite + Tailwind + shadcn) e `backend/` (FastAPI + Supabase + Anthropic SDK).
>
> Vamos refatorar o frontend pra introduzir a **Lia** como interface principal e melhorar drasticamente UX/UI. Esse documento te dá contexto. **Apenas leia e responda "entendido, aguardo próximo prompt"**. Não escreva código ainda.

---

## O produto

**Orbitaia** é uma empresa brasileira que vende "time de marketing virtual" pra PMEs (founders SaaS, e-commerce, imobiliárias). O app `assistente-social-midia` é o produto principal: uma plataforma onde o cliente fala com agentes IA que cuidam de toda a presença digital dele — definição de marca, geração de conteúdo, validação, imagens.

**Diferencial competitivo:** "Time de marketing virtual, não ferramenta de geração de post." A metáfora **não é negociável** — toda decisão de UX/copy reforça isso. Cinco personagens humanas com nomes próprios que se coordenam, não 5 features.

## O time de agentes

Cinco personagens com bio, voz e papel claros:

| Nome  | Papel                          | Quando entra                                         |
|-------|--------------------------------|------------------------------------------------------|
| Lia   | Anfitriã · Cérebro central     | Toda conversa. Recebe pedido, decide quem chamar.    |
| Vega  | Estrategista de Marca          | Quando algo mexe na marca (ICP, voz, posicionamento) |
| Lyra  | Redatora                       | Posts, carrosséis, copy                              |
| Iris  | Revisora de coerência          | Última camada antes de publicar                      |
| Orion | Visual                         | Quando o post pede imagem                            |

Detalhamento completo (bio, sliders, capabilities) virá no PROMPT 02.

## Stack confirmada

**Frontend (`frontend/`):**
- React 19 + Vite + TypeScript
- Tailwind CSS
- shadcn/ui como base (customizada)
- **Roteamento:** `react-router-dom` v6 (instalar se não tiver)
- **Estado global:** `zustand` (instalar se não tiver)
- **Mock backend:** `msw` v2 (Mock Service Worker — instalar se não tiver)
- Fonts via Google Fonts: Manrope (UI), JetBrains Mono (mono), Instrument Serif (acentos)

**Backend (`backend/`):**
- FastAPI + Supabase + Anthropic SDK
- Tabelas com prefixo `mkt_*`
- 5 agentes implementados como classes em `backend/agents/`
- **Não toque no backend nesta refatoração** — só use endpoints existentes ou crie mocks via MSW.

## Princípios que regem a refatoração

**1. Lia é a interface principal, não uma feature.** Bolha flutuante presente em todas as telas autenticadas. Side panel à direita. Persiste contexto entre navegações.

**2. Brand Memory é um organismo vivo, não um formulário.** 7 blocos com estados (completo / parcial / sugestão / vazio), histórico de versões, governança via Mudanças Pendentes. Nunca exigir JSON técnico do usuário.

**3. Outcome-language em vez de jargão técnico.** Slider pergunta "quão crítica ela é com seu conteúdo?" — não "temperature: 0.7". Capability é "bloquear publicação fora do tom" — não "validate_brand_coherence_threshold".

**4. Modo simples por padrão, modo avançado opt-in.** Toggle visível mas nunca empurrado. Power user encontra; leigo nem percebe que existe.

**5. Nada vai pro Brand Memory sem o usuário ver e aprovar.** Toda mudança vira "Mudança Pendente" com diff antes vs depois. Lia consulta antes de escrever.

**6. Densidade controlada.** Scan rápido de informação importante, sem sobrecarregar. Espaços generosos. Tipografia hierárquica. Cores funcionais (laranja = ação, azul = info, verde = sucesso, amarelo = atenção, vermelho = erro).

## Voz da marca (Orbitaia)

- **Direta, técnica, sem corporativês.** Evita "solução end-to-end", "potencialize seu negócio", emojis decorativos.
- **Humor seco quando cabe.** "Make.com no chiclete." "Frankenstein que ninguém mantém." Não tem medo de tomar posição.
- **Trata o usuário como adulto técnico.** Não infantiliza, não explica demais.
- **Português brasileiro real.** "Pra você", não "para você". "Tô", "tá" se cabe no contexto.
- **Sem emoji, exceto raros casos funcionais** (✓ pra check, → pra direção).

## Voz dos agentes

Cada agente tem voz própria que **adapta-se ao tone of voice da marca do tenant** (não usa voz da Orbitaia). Em contexto de demonstração (`tenant=orbitaia`), eles soam técnicos e diretos. Pra um tenant de clínica pediátrica, soariam mais acolhedores. Implementação: cada agente recebe `brand_memory.tone` no contexto e adapta.

A Lia é diferente das outras 4 nesse aspecto: ela é **interface da plataforma**, não da marca. Ela soa como **um colega de time experiente** (mesmo tom independente do tenant). Os outros 4 soam como **especialistas que vestem a marca do cliente**.

## Paleta — manter e refinar

```
--bg-base:       #08070a   (fundo principal — preto quase absoluto)
--bg-elevated:   #111014   (cards, panels)
--bg-card:       #16151a   (containers internos)
--bg-input:      #0d0c10   (campos)

--text-primary:    #f5f4f2
--text-secondary:  #a8a59e
--text-tertiary:   #6b6862
--text-muted:      #45423d

--accent:        #F97316   (laranja Orbitaia — único acento de marca)
--accent-soft:   rgba(249, 115, 22, 0.12)

--success:  #4ade80
--warning:  #fbbf24
--info:     #60a5fa
--danger:   #f87171
```

Acento da Lia é gradient laranja-azul (sinaliza papel híbrido — relacionamento + coordenação). Demais agentes têm cor única (Vega laranja, Lyra verde, Iris amarelo, Orion roxo). Cores são **identidade do agente, não decoração** — usar nas avatars, banners, badges; não em CTAs ou estado de sistema.

## Tipografia

```
--font-sans: 'Manrope', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', ui-monospace, monospace;
--font-serif: 'Instrument Serif', Georgia, serif;
```

**Uso:**
- Sans pra UI geral, headlines, prosa.
- Mono pra labels técnicos, breadcrumbs, badges, timestamps, valores.
- Serif **itálica** pra acentos editoriais — "headline com palavra em destaque", citações dos agentes, avatares com inicial estilizada. Nunca pra prosa longa.

## Microinterações (prioridade alta nesta refatoração)

Você vai implementar com cuidado:

- **Save bar persistente** que aparece em mudanças não salvas, persiste entre navegações, com botões "Descartar" e "Salvar e aplicar"
- **Sliders responsivos** com explicação em itálico embaixo que muda conforme o valor
- **Bolha da Lia** com pulse quando tem sugestão proativa
- **Cascade preview** ao aceitar mudança — "aceitar isso vai disparar 2 sugestões"
- **Toast com id único** que não acumula
- **Animações de entrada** (fade + translate Y, 0.35s cubic-bezier(0.2, 0.8, 0.2, 1))
- **Diff side-by-side** com word-level highlights (verde adição, vermelho riscado)
- **Pulsing live dot** verde nos status "online"
- **Stepper que avança** com check svg quando passo é completado

## Sobre os próximos prompts

Você vai receber em sequência:

- **PROMPT 01** — Design System (tokens, componentes base, configuração de fonts)
- **PROMPT 02** — Agentes (5 personagens, sliders, capabilities, copy)
- **PROMPT 03** — Fluxos e telas (todas as rotas e seus comportamentos)
- **PROMPT 04** — Lia (bolha, side panel, store global, sugestões contextuais)

Cada um vem com critérios de aceite específicos. Implemente em ordem.

---

**Responda apenas:** "Entendido. Tenho contexto da Orbitaia, do time de agentes, da stack, dos princípios e da voz. Aguardando PROMPT 01 com Design System."
