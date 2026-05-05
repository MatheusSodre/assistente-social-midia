# PROMPT 01 — Design System

> **Pré-requisito:** você já leu o PROMPT 00 e tem contexto.
>
> Esta etapa: configurar o design system completo no `frontend/`. Tokens CSS, fontes, componentes base do shadcn customizados, e microinterações compartilhadas. **Não implemente telas ainda** — só fundações.

---

## Setup inicial

Trabalhe em `assistente-social-midia/frontend/`. Verifique `package.json` e instale o que faltar:

```bash
npm install zustand react-router-dom@6 clsx tailwind-merge
npm install -D msw @types/node
```

Se o projeto ainda não tem shadcn configurado, configure agora seguindo a documentação atual em `https://ui.shadcn.com/docs/installation/vite`. Se já tem, apenas valide que está em `src/components/ui/`.

## Arquivo 1 — Tokens globais

Crie `frontend/src/styles/tokens.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

:root {
  /* Backgrounds */
  --bg-base:       #08070a;
  --bg-elevated:   #111014;
  --bg-card:       #16151a;
  --bg-card-hover: #1c1b21;
  --bg-input:      #0d0c10;
  --bg-sidebar:    #0c0b0e;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.05);
  --border-default: rgba(255, 255, 255, 0.09);
  --border-strong:  rgba(255, 255, 255, 0.16);

  /* Text */
  --text-primary:   #f5f4f2;
  --text-secondary: #a8a59e;
  --text-tertiary:  #6b6862;
  --text-muted:     #45423d;

  /* Accent (Orbitaia laranja) */
  --accent:        #F97316;
  --accent-soft:   rgba(249, 115, 22, 0.12);
  --accent-border: rgba(249, 115, 22, 0.35);
  --accent-glow:   rgba(249, 115, 22, 0.20);

  /* Functional colors */
  --success:        #4ade80;
  --success-soft:   rgba(74, 222, 128, 0.10);
  --success-border: rgba(74, 222, 128, 0.30);

  --warning:        #fbbf24;
  --warning-soft:   rgba(251, 191, 36, 0.10);
  --warning-border: rgba(251, 191, 36, 0.30);

  --danger:         #f87171;
  --danger-soft:    rgba(248, 113, 113, 0.10);
  --danger-border:  rgba(248, 113, 113, 0.30);

  --info:           #60a5fa;
  --info-soft:      rgba(96, 165, 250, 0.10);
  --info-border:    rgba(96, 165, 250, 0.30);

  /* Diff highlights (word-level) */
  --diff-add:        rgba(74, 222, 128, 0.20);
  --diff-add-text:   #86efac;
  --diff-remove:     rgba(248, 113, 113, 0.18);
  --diff-remove-text:#fca5a5;

  /* Agent colors (use APENAS em avatars, banners, badges) */
  --agent-vega:  #fb923c;
  --agent-lyra:  #4ade80;
  --agent-iris:  #fbbf24;
  --agent-orion: #c084fc;

  /* Fonts */
  --font-sans:  'Manrope', system-ui, sans-serif;
  --font-mono:  'JetBrains Mono', ui-monospace, monospace;
  --font-serif: 'Instrument Serif', Georgia, serif;

  /* Spacing scale (use múltiplos de 4) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 10px;
  --radius-xl: 14px;
  --radius-2xl: 20px;

  /* Shadow */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.5);
  --shadow-glow-accent: 0 0 0 1px var(--accent), 0 4px 12px var(--accent-glow);
}

/* Map shadcn variables to our tokens */
:root {
  --background: var(--bg-base);
  --foreground: var(--text-primary);
  --card: var(--bg-card);
  --card-foreground: var(--text-primary);
  --popover: var(--bg-elevated);
  --popover-foreground: var(--text-primary);
  --primary: var(--accent);
  --primary-foreground: var(--bg-base);
  --secondary: var(--bg-card);
  --secondary-foreground: var(--text-primary);
  --muted: var(--bg-card);
  --muted-foreground: var(--text-tertiary);
  --accent-bg: var(--bg-card-hover);
  --accent-foreground: var(--text-primary);
  --destructive: var(--danger);
  --destructive-foreground: var(--bg-base);
  --border: var(--border-default);
  --input: var(--border-default);
  --ring: var(--accent);
  --radius: var(--radius-lg);
}

* { box-sizing: border-box; }

html, body {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

body {
  background:
    radial-gradient(ellipse 1000px 500px at 50% -300px, rgba(249, 115, 22, 0.06), transparent 60%),
    var(--bg-base);
}

/* Animations compartilhadas */
@keyframes screenIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.4); opacity: 0; }
}
@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
@keyframes orbPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 60px rgba(249, 115, 22, 0.35); }
  50% { transform: scale(1.05); box-shadow: 0 0 80px rgba(249, 115, 22, 0.55); }
}
@keyframes slideUp {
  from { transform: translate(-50%, 80px); opacity: 0; }
  to { transform: translate(-50%, 0); opacity: 1; }
}
@keyframes toastIn {
  from { opacity: 0; transform: translateX(-50%) translateY(20px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

.screen { animation: screenIn 0.35s cubic-bezier(0.2, 0.8, 0.2, 1); }
```

Importe `tokens.css` no entry point (`main.tsx` ou `index.css`).

## Arquivo 2 — Tailwind config

Atualize `frontend/tailwind.config.js` pra usar as variáveis CSS:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg-base)',
        foreground: 'var(--text-primary)',
        card: 'var(--bg-card)',
        elevated: 'var(--bg-elevated)',
        accent: {
          DEFAULT: 'var(--accent)',
          soft: 'var(--accent-soft)',
          border: 'var(--accent-border)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          DEFAULT: 'var(--border-default)',
          strong: 'var(--border-strong)',
        },
        text: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          tertiary: 'var(--text-tertiary)',
        },
        success: 'var(--success)',
        warning: 'var(--warning)',
        danger: 'var(--danger)',
        info: 'var(--info)',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
        serif: ['var(--font-serif)'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
      },
      animation: {
        'screen-in': 'screenIn 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)',
        'msg-in': 'msgIn 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)',
        'live-pulse': 'livePulse 2s ease-in-out infinite',
        'orb-pulse': 'orbPulse 2.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
```

## Arquivo 3 — Componentes base

Crie/customize estes componentes shadcn (use `npx shadcn@latest add` quando aplicável):

- `Button` — variantes: `default` (laranja sólido), `secondary` (card cinza), `ghost` (transparente), `success`, `danger`. Tamanhos: `sm` (32px), `default` (38px), `lg` (44px). Sempre com `font-medium`.

- `Input` — fundo `--bg-input`, border `--border-default`, focus border `--accent`.

- `Textarea` — mesmo estilo do Input.

- `Badge` — pequeno (font 10px), uppercase, font-mono, padding 2px 7px. Variantes: `success`, `warning`, `info`, `danger`, `neutral`, `accent` (laranja sólido — usar pro estado "sugestão" e contadores importantes).

- `Card` — `--bg-card`, border `--border-default`, radius `--radius-xl`, padding default 16px.

- `Dialog` (modal) — backdrop `rgba(0,0,0,0.6)`, dialog `--bg-card`, max-width 520px, radius `--radius-2xl`.

- `Tooltip` — fundo `--bg-elevated`, font 12px, padding 6px 10px.

- `Toast` (Sonner) — fundo `--bg-card`, border ` --success-border` (sucesso) ou `--danger-border` (erro), animação `toastIn`. Único toast por vez (não acumula).

## Arquivo 4 — Componentes Orbitaia (custom)

Crie em `frontend/src/components/ui/` os componentes reutilizáveis específicos do app:

### `<PageHead />`

Header de cada tela. Props: `eyebrow`, `title`, `titleAccent` (palavra em serif italic laranja, opcional), `sub`, `right` (slot pra ações ou stats).

### `<Stepper />`

Navegação por etapas horizontal. Props: `steps` (array com `{ key, label }`), `currentStep`, `completedSteps`. Cada passo: número/check em círculo + label. Transição suave quando avança. Linhas conectoras entre passos.

### `<MetaPill />`

Badge informativa horizontal com dot colorido + label "key: **value**". Props: `dotColor`, `label`, `value`. Uso: barra de meta-informação no topo de telas (origem da mudança, versão, timestamp).

### `<SaveBar />`

Barra fixa no bottom-center que aparece quando há mudanças não salvas. Props: `text`, `onDiscard`, `onSave`. Animação `slideUp`. **Persiste entre navegações** — implementar via store global (próximo prompt detalha).

### `<EmptyState />`

Estado vazio reutilizável. Props: `icon`, `title`, `desc`, `action` (botão opcional). Padding generoso (60px), ícone com opacidade 0.3.

### `<Avatar />`

Avatar circular com inicial em serif italic. Props: `name`, `color` (`vega` | `lyra` | `iris` | `orion` | `lia` | `user` | custom), `size` (`sm` 22px, `md` 34px, `lg` 52px, `xl` 88px). Para Lia, usar gradient laranja-azul: `linear-gradient(140deg, #fb923c 0%, #f97316 50%, #60a5fa 100%)`.

### `<DiffSide />`

Card de comparação antes/depois. Props: `variant` (`old` | `new`), `version`, `content` (suporta HTML inline com `<span class="add">` e `<span class="rem">`), `note`. Usado no diff de Mudanças Pendentes.

### `<Slider />`

Slider customizado pra config de agentes. **Não use o do shadcn** — construa sobre `<input type="range">` com track/fill/thumb estilizados. Props: `value`, `onChange`, `labelLeft`, `labelRight`, `question`, `explain` (frase em serif italic embaixo). Suportar drag mouse + touch. Veja PROMPT 02 pra contexto de uso.

### `<Capability />`

Card de capability togglável (igual ao do mockup HTML). Props: `name`, `desc`, `enabled`, `onToggle`, `danger` (boolean — se true, mostra tag "automação" amarela).

## Critérios de aceite desta etapa

- [ ] Tokens CSS definidos em `frontend/src/styles/tokens.css` e importados globalmente
- [ ] Tailwind config estendido com tokens
- [ ] Fontes Google carregadas e funcionando (verificar em devtools)
- [ ] shadcn instalado e variáveis mapeadas pros tokens (Card, Button, Dialog renderizam com cores corretas)
- [ ] 9 componentes custom criados em `frontend/src/components/ui/` com TypeScript types
- [ ] Storybook NÃO é necessário — apenas componentes funcionais e tipados
- [ ] Página de teste em `frontend/src/routes/_design.tsx` (rota `/_design`) que renderiza todos os componentes pra você validar visualmente

## Ao terminar, responda

Liste os arquivos criados/modificados (sem código) e diga: "Design system pronto. Aguardando PROMPT 02 com personagens dos agentes."
