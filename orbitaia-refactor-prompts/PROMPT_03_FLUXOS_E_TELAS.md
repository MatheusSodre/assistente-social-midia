# PROMPT 03 — Fluxos, Telas e Estado Global

> **Pré-requisitos:** PROMPT 00, 01, 02 implementados.
>
> Esta etapa: criar todas as telas do app, roteamento, store Zustand, mock backend (MSW), e shell com sidebar. **Não implemente a Lia ainda** (próximo prompt) — só deixe um placeholder pra ela.

---

## Setup do roteamento

Use `react-router-dom` v6. Crie `frontend/src/router.tsx`:

```typescript
import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { OnboardingShell } from './components/layout/OnboardingShell';
// import telas...

export const router = createBrowserRouter([
  // Onboarding (sem sidebar)
  {
    element: <OnboardingShell />,
    children: [
      { path: '/welcome', element: <WelcomeScreen /> },
      { path: '/onboarding/lia', element: <LiaOnboardingScreen /> },
      { path: '/onboarding/ingest', element: <IngestScreen /> },
      { path: '/onboarding/processing', element: <ProcessingScreen /> },
      { path: '/onboarding/review', element: <ReviewScreen /> },
    ],
  },
  // App autenticado (com sidebar + bolha da Lia)
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <Navigate to="/brand-memory" replace /> },
      { path: '/brand-memory', element: <BrandMemoryScreen /> },
      { path: '/brand-memory/block/:blockKey', element: <BlockDetailScreen /> },
      { path: '/brand-memory/session', element: <VegaSessionScreen /> },
      { path: '/fontes', element: <FontesScreen /> },
      { path: '/changes', element: <ChangesScreen /> },
      { path: '/changes/:changeId', element: <ChangeDiffScreen /> },
      { path: '/agents', element: <AgentsListScreen /> },
      { path: '/agents/:agentKey', element: <AgentDetailScreen /> },
      { path: '/workflow', element: <WorkflowScreen /> },
      { path: '/_design', element: <DesignSystemScreen /> }, // já criado
    ],
  },
]);
```

## Estado global (Zustand)

Crie 4 stores separadas em `frontend/src/store/`:

### `useBrandStore.ts`

```typescript
interface BrandStore {
  brandKit: BrandKit | null;
  hasOnboarded: boolean;
  setBrandKit: (kit: BrandKit) => void;
  loadDemoKit: () => void;
  resetBrandKit: () => void;
}
```

Tipo `BrandKit`:

```typescript
export interface BrandBlock {
  content: string;
  source: string;
  confidence: number; // 0-100
  status: 'complete' | 'partial' | 'empty';
  swatches?: string[]; // só pra bloco visual
}

export interface BrandKit {
  brand: BrandBlock;
  icp: BrandBlock;
  tone: BrandBlock;
  visual: BrandBlock;
  topics: BrandBlock;
  competitors: BrandBlock;
  examples: BrandBlock;
}
```

Inclua `INITIAL_KIT` (brand kit demo da Orbitaia) — pegue do mockup HTML standalone na pasta de referência (peça pro usuário se precisar).

**Conteúdo do INITIAL_KIT** (use exato):

- `brand`: "Orbitaia automatiza marketing de PMEs com agentes IA, sem agência cara nem Make.com no chiclete." · source "Site + 38 posts" · confidence 88 · status partial
- `icp`: "Imobiliárias pequenas, founders de SaaS B2B, gestores de marketing de e-commerce SME." · source "Site" · confidence 52 · status partial
- `tone`: "Direto, técnico, com humor seco. Evita corporativês e jargão de marketing." · source "38 posts Instagram" · confidence 76 · status partial
- `visual`: "Sans-serif geométrica, ícones lineares, fundo escuro com destaque laranja." · source "Site (CSS extraído)" · confidence 92 · swatches ["#080808", "#F97316", "#FFFFFF"] · status partial
- `topics`: "Automação · Agentes IA · Make.com · Cases reais. Quatro pilares de conteúdo identificados." · source "38 posts (clusterização)" · confidence 84 · status partial
- `competitors`: "Vega não inferiu sem ICP fechado. Resolva ICP primeiro pra ela mapear concorrentes." · source "—" · confidence 0 · status empty
- `examples`: "Cole posts seus que deram certo (ou referências) — Vega usa pra calibrar a voz dos agentes." · source "—" · confidence 0 · status empty

### `useChangesStore.ts`

Mudanças pendentes (Brand Memory governance):

```typescript
interface PendingChange {
  id: string;
  block: string;        // nome humano
  blockKey: string;     // 'icp', 'tone', etc
  source: 'session' | 'cascade' | 'manual';
  sourceLabel: string;  // 'sessão · você aceitou'
  fromVersion: string;
  toVersion: string;
  when: string;         // 'há 2 min'
  old: string;
  oldNote: string;
  new: string;
  newNote: string;
  diffOld: string;      // HTML com <span class="rem">
  diffNew: string;      // HTML com <span class="add">
  cascades: { block: string; text: string }[];
}

interface ChangesStore {
  changes: PendingChange[];
  acceptChange: (id: string) => void;
  rejectChange: (id: string) => void;
  acceptAll: () => void;
  resetChanges: () => void;
}
```

Inclua `INITIAL_CHANGES` com 3 mudanças demo (1 da sessão da Vega + 2 cascades). Use o conteúdo abaixo:

**Change 1** (id 'c1', source 'session'):
- block: 'Pra quem você fala', blockKey: 'icp', from v1 to v2
- old: "Imobiliárias pequenas, founders de SaaS B2B, gestores de marketing de e-commerce SME."
- new: "Founder de SaaS B2B (primário). Imobiliárias e e-commerce SME como secundários. Dor: postar consistente sem virar refém de agência ou Make.com."
- cascades: [{ block: 'Como você soa', text: 'voz vai ser ajustada pra registro técnico' }, { block: 'Sobre o que você fala', text: 'novo pilar "founder vida real" sugerido' }]

**Change 2** (id 'c2', source 'cascade'):
- block: 'Como você soa', blockKey: 'tone'
- old: "Direto, técnico, com humor seco. Evita corporativês."
- new: "Direto, técnico-pragmático, com humor seco. Linguagem de founder pra founder — usa 'você' sempre, nunca 'a empresa'."

**Change 3** (id 'c3', source 'cascade'):
- block: 'Sobre o que você fala', blockKey: 'topics'
- old: "Automação · Agentes IA · Make.com · Cases reais. Quatro pilares de conteúdo."
- new: "Automação · Agentes IA · Make.com · Cases reais · Founder vida real. Cinco pilares de conteúdo."

### `useFontesStore.ts`

```typescript
type FonteType = 'website' | 'instagram' | 'linkedin' | 'pdf' | 'chat';
type FonteStatus = 'indexed' | 'processing' | 'error';

interface Fonte {
  id: string;
  type: FonteType;
  name: string;
  url: string;
  status: FonteStatus;
  stats: { items: string; time: string };
}

interface FontesStore {
  fontes: Fonte[];
  addFonte: (f: Omit<Fonte, 'id'>) => void;
  removeFonte: (id: string) => void;
  reindexFonte: (id: string) => void;
  resetFontes: () => void;
}
```

Demo seed (3 fontes):

- orbitaia.com.br · website · indexed · 12 páginas
- @orbitaia · instagram · indexed · 38 posts
- plano-marketing-2026.pdf · pdf · indexed · 15 páginas

### `useAgentsStore.ts`

```typescript
interface AgentConfig {
  sliders: Record<string, number>;
  capabilities: Record<string, boolean>;
}

interface AgentsStore {
  configs: Record<AgentKey, AgentConfig>;
  hasUnsavedChanges: boolean;
  updateSlider: (agent: AgentKey, sliderKey: string, value: number) => void;
  toggleCapability: (agent: AgentKey, capKey: string) => void;
  saveChanges: () => void;
  discardChanges: () => void;
}
```

Inicialize `configs` a partir dos defaults em `AGENTS` (PROMPT 02).

## Mock backend (MSW)

Configure MSW em `frontend/src/mocks/`:

- `handlers.ts` — handlers que retornam dados das stores acima
- `browser.ts` — `setupWorker(...handlers)`
- `server.ts` (opcional, pra testes)

Endpoints mockados (todos retornam dados das stores):

```
GET  /api/brand-kit           → BrandKit
GET  /api/changes             → PendingChange[]
POST /api/changes/:id/accept  → 200
POST /api/changes/:id/reject  → 200
GET  /api/fontes              → Fonte[]
POST /api/fontes              → Fonte (com simulated delay 2.5s pra status virar 'indexed')
DELETE /api/fontes/:id        → 200
GET  /api/agents              → Agent[] (de data/agents.ts)
GET  /api/agents/:key/config  → AgentConfig
PATCH /api/agents/:key/config → 200
```

Inicialize MSW em `main.tsx`:

```typescript
async function enableMocking() {
  const { worker } = await import('./mocks/browser');
  return worker.start();
}
enableMocking().then(() => {
  // render React
});
```

## Layouts

### `<OnboardingShell />`

Container full-bleed (sem sidebar). Centra conteúdo verticalmente. Background com gradient radial laranja sutil no topo. `<Outlet />` no centro.

### `<AppShell />`

Layout com sidebar fixa à esquerda + área principal. Use **flex** (não grid):

```
[sidebar 244px fixed] [main-area flex-1 min-w-0]
                       [topbar sticky]
                       [<Outlet />]
                       [<LiaBubble />]  ← placeholder por enquanto, próximo prompt
```

Em telas <880px, sidebar vira drawer com hamburger no canto superior esquerdo. Backdrop ao abrir, fecha ao clicar fora ou navegar.

### `<Sidebar />`

3 seções com headers em font-mono uppercase:

**Marca:**
- Brand Memory (icon ◇) → /brand-memory
- Fontes (icon ⊕, badge dim com count) → /fontes
- Mudanças pendentes (icon ⤳, badge laranja sólido com count) → /changes

**Time:**
- Lia (icon ★ laranja, badge dim "anfitriã") → /agents/lia
- Outros agentes (icon ★, badge dim "4") → /agents
- Fluxo de trabalho (icon →) → /workflow

**Operação** (cinza, desabilitado por enquanto):
- Gerar conteúdo (badge dim "soon")
- Histórico

**Footer:** card com avatar + nome + tenant ("Matheus / orbitaia").

## Telas

### `/welcome` — Welcome

Landing inicial. Eyebrow pill, título "Conheça a Lia, sua anfitriã" (com "Lia" em serif italic laranja), subtítulo, 3 cards de início:

1. **Tenho site ou Instagram** → /onboarding/ingest
2. **Tenho material em PDF** → /onboarding/ingest
3. **Conversar com a Lia** → /onboarding/lia

Footer: atalho dev "já tenho brand kit, vai pro app" → loadDemoKit() + navigate('/brand-memory').

### `/onboarding/lia` — Chat tela cheia da Lia

Card central (max-w 640px) com:
- Header: avatar gradient mixed, "Lia / anfitriã · primeiro contato", botão fechar
- Área de mensagens: 3 mensagens iniciais da Lia se apresentando e fazendo a primeira pergunta ("qual o nome da sua empresa e o que ela faz?")
- Sugestões: chips "Responder de exemplo" e "Pular"
- Input com textarea + botão enviar

Após 3 turnos do usuário, Lia oferece action card "Pode chamar a Vega" → leva pra /onboarding/processing.

### `/onboarding/ingest`

Form com 3 field-groups: site, instagram, materiais (upload zone com drag-drop). Botão primário "Vega vai ler tudo →" → /onboarding/processing.

### `/onboarding/processing`

Animação de orb pulsante (gradient laranja) + lista vertical de 8 steps que vão sendo marcados (active → done) com timing aleatório 500-850ms. Auto-navega pra /onboarding/review ao terminar. Steps:

1. Lendo orbitaia.com.br · 12 páginas
2. Analisando 38 posts do @orbitaia · Instagram API
3. Processando PDFs anexados · 15 páginas
4. Identificando posicionamento · sonnet 4.6
5. Mapeando voz e tom · haiku 4.5
6. Extraindo identidade visual · CSS + imagens
7. Clusterizando temas em pilares · embeddings
8. Montando brand kit inicial · sonnet 4.6

### `/onboarding/review`

Pill "primeira leitura · revise antes de salvar" + título "Aqui está o que Vega entendeu da sua marca" + grid dos 7 blocos com confidence %. Dois CTAs: "Aceitar tudo e ir pro app" → /brand-memory; "Conversar com a Vega pra refinar" → /brand-memory/session.

### `/brand-memory` — Dashboard principal

`<PageHead>` com eyebrow "brand memory · orbitaia", título "Sua marca, em 7 blocos", subtítulo. À direita: bar de completude (% e count de pendentes).

Banner proativo da Vega (gradient laranja sutil): avatar V, "Vega notou 3 pontos a melhorar", CTA "Vamos resolver →" → /brand-memory/session.

Grid dos 7 blocos como cards clicáveis (vão pra /brand-memory/block/:key). Cada card: nome, status badge, conteúdo truncado, fonte, % confidence.

Dois CTAs grandes embaixo: "Conversar com a Vega" e "Configurar agentes" → /agents.

### `/brand-memory/block/:blockKey`

Detalhe do bloco. Botão voltar. PageHead com eyebrow "brand memory · {short}" e título do bloco. Card grande com conteúdo atual. Grid de 3 meta-cards (Fonte, Confiança, Versão). Ações: "Conversar com Vega →", "Editar manualmente", "Ver histórico".

### `/brand-memory/session` — Sessão da Vega (chat)

Botão voltar. PageHead "Resolver 3 lacunas". Card central com chat da Vega: 1 mensagem inicial explicando ordem (ICP, Concorrentes, Exemplos), seguida da proposta de ICP com dor mapeada em quote box (serif italic).

Botões: "Compra essa proposta" → gera 3 mudanças e navega pra /changes; "Ajustar a dor"; "Trocar persona".

### `/fontes`

Botão "+ Adicionar fonte" no header (abre modal). Grid de fonte-cards. Card "+ adicionar nova fonte" tracejado no fim do grid. Banner inferior: "Lia também recebe fontes pelo chat" + botão "Falar com a Lia" (abre LiaBubble).

Modal de adicionar: tipo (4 botões: Site, Instagram, LinkedIn, Arquivos), input URL, botão "Adicionar e indexar →".

### `/changes` — Mudanças pendentes

Se vazio: empty state. Se tem mudanças: bulk bar (count + "Aceitar todas") + lista de change-cards com diff preview (antes / → / depois truncados). Click no card → /changes/:id.

### `/changes/:changeId`

Diff completo. Meta-bar com 3 pills (origem, versão, when). Grid de 2 cards (antes / depois) com word-level highlights. Cascade card se houver. Ações: "Voltar e ajustar", "Salvar essa versão →".

### `/agents` — Lista do time

Status bar (time online · stats da semana). Grid de 5 agent-cards (banner gradient + avatar + nome + role + tagline + 2 stats). Click leva pra /agents/:key.

### `/agents/:agentKey`

Hero com avatar 88px, nome 38px, role mono, bio. Meta pills (status, model). Toggle "Configuração simples ↔ Modo avançado".

**Modo simples:** card de sliders (3-4 sliders por agente, conforme PROMPT 02) + card de capabilities.

**Modo avançado:** parâmetros do modelo (select + temperature + max_tokens + timeout) + system prompt em mono.

Painel direito sticky: preview ao vivo da config atual.

Save bar fixa no bottom-center quando há `hasUnsavedChanges`.

### `/workflow`

Diagrama horizontal: trigger "você pede algo" → Lia → bifurca pra Vega/Lyra → Orion → Iris → "✓ entrega". Cada nó é clicável (vai pra /agents/:key). Background com grid sutil.

Embaixo: "regras de handoff" — grid de 5 cards (de HANDOFFS).

## Critérios de aceite

- [ ] react-router-dom v6 configurado com layouts
- [ ] 4 stores Zustand criadas e populadas com seeds
- [ ] MSW configurado com handlers e seed data
- [ ] AppShell com sidebar funcional + drawer mobile
- [ ] OnboardingShell sem sidebar
- [ ] Todas as 14 telas implementadas (placeholder simples se necessário)
- [ ] Navegação fluida entre telas (sidebar atualiza estado ativo)
- [ ] LiaBubble: deixar componente vazio `<LiaBubble />` no AppShell — só placeholder

## Ao terminar

Liste arquivos criados e diga: "Fluxos e telas prontos. Aguardando PROMPT 04 com Lia."
