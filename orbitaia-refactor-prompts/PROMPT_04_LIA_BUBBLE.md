# PROMPT 04 — Lia: Bolha Flutuante e Side Panel

> **Pré-requisitos:** PROMPTs 00, 01, 02, 03 implementados.
>
> Esta etapa final: implementar a Lia como interface principal do app. Bolha flutuante presente em todas as telas autenticadas, side panel com chat, store dedicada, sugestões contextuais, ingestão de arquivos via chat.

---

## Store da Lia

Crie `frontend/src/store/useLiaStore.ts`:

```typescript
import { create } from 'zustand';

export type LiaMessageRole = 'lia' | 'user';

export interface LiaActionButton {
  label: string;
  primary?: boolean;
  action: string; // chave de uma ação registrada (ver lia-actions.ts)
}

export interface LiaActionCard {
  label: string;        // "próxima ação" — acima dos botões
  text: string;
  buttons: LiaActionButton[];
}

export interface LiaMessage {
  id: string;
  role: LiaMessageRole;
  text: string;          // suporta <strong>
  action?: LiaActionCard;
  timestamp: number;
}

export interface LiaSuggestion {
  label: string;     // chip que aparece embaixo das mensagens
  action: string;    // chave registrada em lia-actions.ts
}

interface LiaStore {
  open: boolean;
  hasSuggestion: boolean;        // controla pulse no badge da bolha
  messages: LiaMessage[];
  pendingAction: string | null;   // se a Lia espera resposta do user

  openLia: () => void;
  closeLia: () => void;
  toggleLia: () => void;

  pushMessage: (msg: Omit<LiaMessage, 'id' | 'timestamp'>) => void;
  pushUserMessage: (text: string) => void;
  pushLiaMessage: (text: string, action?: LiaActionCard) => void;
  clearMessages: () => void;

  setHasSuggestion: (v: boolean) => void;
}

export const useLiaStore = create<LiaStore>((set, get) => ({
  open: false,
  hasSuggestion: false,
  messages: [],
  pendingAction: null,

  openLia: () => set({ open: true, hasSuggestion: false }),
  closeLia: () => set({ open: false }),
  toggleLia: () => set(s => ({ open: !s.open, hasSuggestion: s.open ? s.hasSuggestion : false })),

  pushMessage: (msg) => set(s => ({
    messages: [...s.messages, { ...msg, id: crypto.randomUUID(), timestamp: Date.now() }],
  })),
  pushUserMessage: (text) => get().pushMessage({ role: 'user', text }),
  pushLiaMessage: (text, action) => get().pushMessage({ role: 'lia', text, action }),
  clearMessages: () => set({ messages: [] }),

  setHasSuggestion: (v) => set({ hasSuggestion: v }),
}));
```

## Sugestões contextuais por rota

Crie `frontend/src/lib/lia-suggestions.ts`:

```typescript
import type { LiaSuggestion } from '@/store/useLiaStore';

export function getSuggestionsForRoute(pathname: string): LiaSuggestion[] {
  if (pathname.startsWith('/brand-memory')) {
    return [
      { label: 'Como adiciono uma fonte?', action: 'how-fonte' },
      { label: 'Resolver lacunas pendentes', action: 'gaps' },
      { label: 'O que é Brand Memory?', action: 'help-bm' },
    ];
  }
  if (pathname.startsWith('/agents')) {
    return [
      { label: 'Como configuro a Lyra?', action: 'help-lyra' },
      { label: 'Diferença entre os agentes', action: 'help-agents' },
    ];
  }
  if (pathname.startsWith('/changes')) {
    return [
      { label: 'O que são mudanças cascade?', action: 'help-cascade' },
      { label: 'Posso reverter depois?', action: 'help-revert' },
    ];
  }
  if (pathname.startsWith('/fontes')) {
    return [
      { label: 'Adicionar Instagram', action: 'add-ig' },
      { label: 'Anexar PDF do plano', action: 'add-pdf' },
    ];
  }
  if (pathname.startsWith('/workflow')) {
    return [
      { label: 'Por que 5 agentes?', action: 'help-agents' },
    ];
  }
  return [
    { label: 'Como funciona o app?', action: 'help-app' },
    { label: 'Gerar 3 posts pra testar', action: 'gen' },
  ];
}

export function getContextLabel(pathname: string): string {
  if (pathname.startsWith('/brand-memory/block')) return 'Detalhe do bloco';
  if (pathname.startsWith('/brand-memory/session')) return 'Sessão com a Vega';
  if (pathname.startsWith('/brand-memory')) return 'Brand Memory';
  if (pathname.startsWith('/changes')) return 'Mudanças pendentes';
  if (pathname.startsWith('/fontes')) return 'Fontes';
  if (pathname.startsWith('/agents')) return 'Time de agentes';
  if (pathname.startsWith('/workflow')) return 'Fluxo de trabalho';
  return 'app';
}
```

## Ações da Lia

Crie `frontend/src/lib/lia-actions.ts`. Mapa de `actionKey → handler`:

```typescript
import { useLiaStore } from '@/store/useLiaStore';
import { useFontesStore } from '@/store/useFontesStore';
import { useNavigate } from 'react-router-dom';

type LiaActionResponse = {
  text: string;
  action?: import('@/store/useLiaStore').LiaActionCard;
  followup?: string;
};

const RESPONSES: Record<string, LiaActionResponse> = {
  'help-bm': {
    text: '<strong>Brand Memory</strong> é o conjunto de 7 blocos que define sua marca. Cada bloco é uma faceta — quem você é, com quem fala, como soa, etc. Os agentes leem isso antes de produzir qualquer conteúdo.',
    followup: 'Quer que eu te leve lá?',
  },
  'gaps': {
    text: 'Você tem 3 blocos pendentes — Concorrentes, Exemplos e ICP precisa de dor mapeada. Quer que eu chame a Vega pra resolver?',
    action: {
      label: 'próxima ação',
      text: 'Vega vai te entrevistar em ~8 min e refinar os 3 blocos.',
      buttons: [
        { label: 'Chamar Vega', primary: true, action: 'go-session' },
        { label: 'Agora não', action: 'dismiss' },
      ],
    },
  },
  'help-lyra': {
    text: '<strong>Lyra</strong> é a redatora — escreve posts, carrosséis e copy. Você configura ela em <em>Time → Outros agentes → Lyra</em>. Os principais sliders são: voz (conservadora/ousada), tamanho de post, e tipo de gancho.',
    followup: 'Quer que eu abra a config dela?',
  },
  'help-agents': {
    text: 'Você tem 5 agentes: <strong>Lia</strong> (eu, anfitriã), <strong>Vega</strong> (estrategista de marca), <strong>Lyra</strong> (escreve), <strong>Iris</strong> (revisa) e <strong>Orion</strong> (gera imagens). Cada um faz uma coisa específica e bem feita.',
  },
  'help-cascade': {
    text: 'Cascade é quando uma mudança em um bloco automaticamente sugere ajustes em outros. Por exemplo: se você muda o ICP, a Vega sugere ajustar Voz e Pilares também — porque eles dependem do ICP.',
  },
  'help-revert': {
    text: 'Sim, sempre. Cada bloco tem histórico de versões — você pode reverter pra qualquer versão antiga, e a versão atual fica preservada como nova versão no histórico. Nada é perdido.',
  },
  'help-app': {
    text: 'Resumo rápido: você adiciona <strong>Fontes</strong> (site, Insta, PDFs) → eu e a Vega lemos e montamos seu <strong>Brand Memory</strong> (7 blocos da marca) → você configura os <strong>Agentes</strong> (Lyra, Iris, Orion) → e gera conteúdo. Eu te acompanho em todo o processo.',
  },
  'add-ig': {
    text: 'Beleza. Manda o handle (@nomedoinsta) ou o link completo aqui no chat. Eu indexo os últimos 50 posts e atualizo as Fontes.',
  },
  'add-pdf': {
    text: 'Pode arrastar o PDF aqui no chat ou clicar no botão "+" do input. Eu leio o conteúdo e adiciono na lista de Fontes pra Vega usar.',
  },
  'how-fonte': {
    text: 'Você pode (1) ir na seção <strong>Fontes</strong> no menu lateral e clicar em "Adicionar fonte", ou (2) me mandar o link/arquivo aqui no chat — eu cuido da indexação.',
  },
  'gen': {
    text: 'Geração de posts ainda está em desenvolvimento — a tela tá marcada como "soon" no menu. Por enquanto, você pode configurar a Lyra pra ela ficar pronta.',
  },
};

export function dispatchLiaAction(actionKey: string, navigate?: ReturnType<typeof useNavigate>) {
  const lia = useLiaStore.getState();

  // ações de navegação
  if (actionKey === 'go-session') {
    lia.closeLia();
    navigate?.('/brand-memory/session');
    return;
  }
  if (actionKey === 'dismiss') {
    lia.pushLiaMessage('Tranquilo. Quando quiser é só falar.');
    return;
  }
  if (actionKey === 'confirm-fonte') {
    const newFonte = {
      type: 'pdf' as const,
      name: 'plano-marketing.pdf',
      url: '2.4 MB',
      status: 'indexed' as const,
      stats: { items: '12 páginas', time: 'agora' },
    };
    useFontesStore.getState().addFonte(newFonte);
    lia.pushLiaMessage('<strong>Pronto.</strong> Adicionado em Fontes e indexado. Vega vai propor mudanças no Brand Memory baseadas nesse plano — você revisa em "Mudanças Pendentes".');
    return;
  }

  // ações de resposta
  const resp = RESPONSES[actionKey];
  if (resp) {
    const text = resp.text + (resp.followup ? '<br><br>' + resp.followup : '');
    lia.pushLiaMessage(text, resp.action);
  }
}

export function liaAttach(filename = 'plano-marketing.pdf') {
  const lia = useLiaStore.getState();
  lia.pushUserMessage(`📎 [arquivo: ${filename}]`);
  setTimeout(() => {
    lia.pushLiaMessage(
      `Recebi o PDF. Vou indexar e adicionar como fonte.`,
      {
        label: 'confirmar ação',
        text: `Adicionar "${filename}" às Fontes e processar conteúdo?`,
        buttons: [
          { label: 'Pode adicionar', primary: true, action: 'confirm-fonte' },
          { label: 'Cancelar', action: 'dismiss' },
        ],
      }
    );
  }, 600);
}
```

## Componente `<LiaBubble />`

Crie `frontend/src/components/lia/LiaBubble.tsx`:

```typescript
import { useLiaStore } from '@/store/useLiaStore';
import { LiaPanel } from './LiaPanel';

export function LiaBubble() {
  const { open, hasSuggestion, openLia } = useLiaStore();

  return (
    <>
      {!open && (
        <button
          onClick={openLia}
          className="lia-bubble"
          aria-label="Abrir chat com a Lia"
          data-pulse={hasSuggestion}
        >
          L
        </button>
      )}
      <LiaPanel />
    </>
  );
}
```

CSS pra `.lia-bubble` (em `tokens.css` ou `lia.css`):

```css
.lia-bubble {
  position: fixed;
  bottom: 22px; right: 22px;
  width: 56px; height: 56px;
  border-radius: 50%;
  background: linear-gradient(140deg, #fb923c 0%, #f97316 50%, #60a5fa 100%);
  border: 2px solid var(--bg-base);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  z-index: 70;
  box-shadow: 0 8px 32px rgba(249, 115, 22, 0.35), 0 4px 12px rgba(0,0,0,0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  font-family: var(--font-serif); font-style: italic;
  font-size: 26px; color: var(--bg-base); font-weight: 400;
}
.lia-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(249, 115, 22, 0.5), 0 6px 16px rgba(0,0,0,0.5);
}
.lia-bubble[data-pulse="true"]::after {
  content: '';
  position: absolute;
  top: 4px; right: 4px;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--bg-base);
  animation: pulse 2s ease-in-out infinite;
}
```

## Componente `<LiaPanel />`

Side panel que desliza da direita. Renderiza:

1. **Header**: avatar Lia + nome + status "online" (live dot verde) + label de contexto ("vendo: Brand Memory") + botão fechar.

2. **Área de mensagens**: scrollable, mostra todas as mensagens de `useLiaStore.messages` via `<LiaMessage />`.

3. **Sugestões contextuais**: se houver, mostra chips embaixo das mensagens. Pega de `getSuggestionsForRoute(location.pathname)`. Click dispara `dispatchLiaAction(suggestion.action)`.

4. **Input area**: textarea + botão de anexar (+) + botão de enviar (→). Enter envia, Shift+Enter quebra linha. Anexar dispara `liaAttach()` (mock).

CSS principal:

```css
.lia-panel {
  position: fixed;
  top: 0; right: 0;
  width: 400px;
  max-width: 92vw;
  height: 100vh;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border-default);
  z-index: 75;
  display: flex; flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.4);
}
.lia-panel[data-open="true"] {
  transform: translateX(0);
}

.lia-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 72;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}
.lia-backdrop[data-show="true"] {
  opacity: 1;
  pointer-events: auto;
}

@media (max-width: 600px) {
  .lia-panel { width: 100vw; max-width: 100vw; }
}
```

## Componente `<LiaMessage />`

Renderiza uma mensagem individual:

- Avatar circular pequeno (28px) à esquerda (Lia) ou direita (user)
- Bubble com radius assimétrico (top-left curto pra Lia, top-right curto pro user)
- Lia: bg `--bg-card`, border `--border-default`. User: bg `--accent`, color `--bg-base`.
- Texto suporta `<strong>` (use `dangerouslySetInnerHTML` aqui — texto é controlado por nós)
- Se tem `action`, renderiza `<LiaActionCard />` dentro do bubble

Animação `msgIn` quando entra.

## Componente `<LiaActionCard />`

Card menor dentro da bolha de mensagem da Lia:

```
┌────────────────────────────┐
│ PRÓXIMA AÇÃO               │  ← label uppercase mono accent
│ Texto explicando...        │
│ [Botão primary]  [Botão]   │
└────────────────────────────┘
```

bg `--bg-input`, border `--border-default`, padding 10px 12px.

## Comportamentos contextuais

A Lia deve **inicializar mensagens** quando o painel é aberto pela primeira vez:

```typescript
// Em LiaPanel, useEffect:
useEffect(() => {
  if (open && messages.length === 0) {
    const ctxLabel = getContextLabel(pathname);
    pushLiaMessage(`Oi! Estou aqui se precisar. Você está em <strong>${ctxLabel}</strong>.`);
    pushLiaMessage('Posso te explicar como algo funciona, ajudar a adicionar fontes, ou conversar com a Vega pra refinar sua marca. O que você quer fazer?');
  }
}, [open, messages.length, pathname]);
```

## Integração no AppShell

Substitua o placeholder `<LiaBubble />` no `AppShell` (PROMPT 03) pelo componente real. A bolha aparece em **todas as telas autenticadas**, mas **não em onboarding** (`OnboardingShell` não a renderiza).

## Critérios de aceite

- [ ] Store Zustand `useLiaStore` criada
- [ ] `lia-suggestions.ts` com sugestões por rota
- [ ] `lia-actions.ts` com mapa de ações
- [ ] Componentes: LiaBubble, LiaPanel, LiaMessage, LiaActionCard
- [ ] Bolha aparece em todas as telas do AppShell, não em OnboardingShell
- [ ] Click na bolha abre side panel com slide-in da direita
- [ ] Mensagens iniciais aparecem na primeira abertura
- [ ] Sugestões contextuais mudam conforme a rota
- [ ] Click em sugestão dispara resposta da Lia
- [ ] Botão "+" anexar dispara fluxo de adicionar PDF mockado
- [ ] Confirmação "Pode adicionar" insere fonte real no `useFontesStore`
- [ ] Mensagens persistem entre navegações (não são limpas ao trocar de tela)
- [ ] Mobile: panel ocupa 100% da largura
- [ ] Backdrop ao abrir, fecha clicando fora

## Ao terminar

Liste arquivos criados e diga: "App completo implementado. Próximos passos: conectar backend real e implementar tela de Geração de Conteúdo."
