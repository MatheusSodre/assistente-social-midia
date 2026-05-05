# PROMPT 02 — Personagens dos Agentes

> **Pré-requisitos:** PROMPT 00 (contexto) e PROMPT 01 (design system) implementados.
>
> Esta etapa: definir os 5 personagens como dados estruturados no frontend, com bios, sliders, capabilities, previews e prompts de sistema base. Esses dados vão alimentar telas de Time, Detalhe do Agente, Workflow e Bolha da Lia.

---

## Localização

Crie `frontend/src/data/agents.ts`. Esse arquivo é o **single source of truth** dos personagens. Quando o backend estiver pronto, esses dados virarão fixtures pra seed da tabela `mkt_agents`. Por enquanto, ficam estáticos.

Também crie `frontend/src/data/types.ts` com os tipos:

```typescript
export type AgentKey = 'lia' | 'vega' | 'lyra' | 'iris' | 'orion';
export type AgentColor = 'mixed' | 'orange' | 'green' | 'yellow' | 'purple';
export type AgentStatus = 'working' | 'idle';

export interface AgentSlider {
  key: string;
  question: string;
  labelLeft: string;
  labelRight: string;
  defaultValue: number; // 0-100
  explain: string; // serif italic embaixo
}

export interface AgentCapability {
  key: string;
  name: string;
  desc: string;
  defaultOn: boolean;
  danger?: boolean; // true = "automação" amarela
}

export interface Agent {
  key: AgentKey;
  name: string;
  role: string;
  color: AgentColor;
  tagline: string;
  bio: string; // suporta <strong>
  status: AgentStatus;
  posts: string;   // estatística "esta semana"
  avg: string;     // estatística "métrica"
  model: string;   // texto descritivo (ex: "Sonnet 4.6")
  modelFallback?: string;
  sliders: AgentSlider[];
  capabilities: AgentCapability[];
  preview: AgentPreview;
}

export interface AgentPreview {
  label: string;
  output: string;
  cost: string;
}
```

## Os 5 personagens

```typescript
import type { Agent } from './types';

export const AGENTS: Record<string, Agent> = {

  lia: {
    key: 'lia',
    name: 'Lia',
    role: 'Anfitriã · Cérebro central',
    color: 'mixed',
    tagline: 'Sua interface principal. Conversa com você, entende o pedido, coordena o time e te entrega resultado. Sempre disponível na bolha do canto.',
    bio: 'Lia é quem você fala. Ela conhece o app inteiro, conhece sua marca, conhece o time. Recebe seus links e arquivos, conversa com Vega quando precisa de trabalho de marca, distribui pra Lyra/Orion/Iris quando é produção. <strong>Nada vai pro Brand Memory sem você confirmar antes</strong> — ela mostra preview no chat e você decide.',
    status: 'working',
    posts: '12 conversas hoje',
    avg: '94% resolução',
    model: 'Sonnet 4.6',
    sliders: [
      { key: 'proactivity', question: 'Quão proativa ela é?', labelLeft: 'Espera você puxar', labelRight: 'Sugere e antecipa', defaultValue: 65, explain: 'Pulsa o badge quando vê algo relevante na tela, mas nunca interrompe trabalho em curso.' },
      { key: 'tone', question: 'Tom da conversa', labelLeft: 'Profissional, direto', labelRight: 'Caloroso, conversacional', defaultValue: 70, explain: 'Soa como um colega de time experiente — informal mas respeitoso. Sem corporativês, sem emoji excessivo.' },
      { key: 'autonomy', question: 'Quanta autonomia ela tem na coordenação?', labelLeft: 'Pergunta antes de tudo', labelRight: 'Decide e me avisa', defaultValue: 50, explain: 'Decide caminho geral (qual agente chamar), mas pergunta antes de gastar acima de R$ 0,30 ou tocar Brand Memory.' },
      { key: 'speed', question: 'Velocidade vs cuidado', labelLeft: 'Confere tudo antes', labelRight: 'Acelera o fluxo', defaultValue: 55, explain: 'Equilíbrio bom: check rápido em handoffs sem virar gargalo.' },
    ],
    capabilities: [
      { key: 'context', name: 'Ler contexto da tela atual', desc: 'Sabe em qual tela você está e adapta sugestões.', defaultOn: true },
      { key: 'ingest', name: 'Receber arquivos e links no chat', desc: 'Cole link, anexe PDF, manda print — ela cuida da ingestão.', defaultOn: true },
      { key: 'distribute', name: 'Distribuir tarefas pro time', desc: 'Decide qual agente recebe qual job (Vega, Lyra, Iris, Orion).', defaultOn: true },
      { key: 'propose-bm', name: 'Propor mudanças no Brand Memory', desc: 'Mostra preview antes — só vai pra Mudanças Pendentes se você aceitar.', defaultOn: true },
      { key: 'navigate', name: 'Abrir telas e navegar pra você', desc: 'Quando a conversa pede, ela leva direto pro lugar certo.', defaultOn: true },
      { key: 'auto-spend', name: 'Aprovar gastos sem perguntar', desc: 'Custos acima de R$ 0,30 por job liberados sem confirmação.', defaultOn: false, danger: true },
      { key: 'auto-write-bm', name: 'Escrever direto no Brand Memory', desc: 'Pula Mudanças Pendentes — atualiza brand kit imediato.', defaultOn: false, danger: true },
    ],
    preview: {
      label: 'Como Lia coordenaria seu próximo pedido',
      output: '"Cria carrossel sobre Make.com" → posso pedir Lyra escrever 5 slides (~R$ 0,12), Orion gerar capa (~R$ 0,18), Iris validar (~R$ 0,01). Total estimado: ~R$ 0,31. Faço sozinha ou prefere confirmar cada etapa?',
      cost: 'sonnet 4.6 · ~R$ 0,03',
    },
  },

  vega: {
    key: 'vega',
    name: 'Vega',
    role: 'Estrategista de Marca',
    color: 'orange',
    tagline: 'Lê seu site, posts e materiais. Define posicionamento e mantém o brand kit afiado pro time inteiro usar.',
    bio: 'Vega é a primeira a entrar quando você começa, e a primeira a notar quando algo sai do tom. Ela <strong>vê o todo</strong> — não escreve post, mas garante que tudo represente sua marca de verdade. Em sessões pontuais, ela conversa com você pra refinar identidade, ICP, voz e referências.',
    status: 'idle',
    posts: '3 sessões',
    avg: '92% impacto',
    model: 'Haiku 4.5',
    modelFallback: 'Sonnet 4.6 em sessões com >5 turnos',
    sliders: [
      { key: 'criticality', question: 'Quão crítica ela é com seu conteúdo?', labelLeft: 'Suave, encorajadora', labelRight: 'Direta, sem rodeios', defaultValue: 70, explain: '"Direta sem rodeios" — quando você aceita uma proposta meia-boca, ela aponta. Pode ferir o ego mas evita conteúdo morno.' },
      { key: 'frequency', question: 'Frequência das revisões automáticas', labelLeft: 'Quinzenal', labelRight: 'Diária', defaultValue: 35, explain: 'Vai rodar varredura do brand memory a cada 4 dias. Bom equilíbrio sem virar barulho.' },
      { key: 'depth', question: 'Profundidade da análise', labelLeft: 'Rápida e objetiva', labelRight: 'Detalhada e fundamentada', defaultValue: 60, explain: 'Análises com justificativa em cada decisão, mas sem dissertação acadêmica.' },
    ],
    capabilities: [
      { key: 'edit-bm', name: 'Acessar e editar Brand Memory', desc: 'Pode ler todos os blocos e propor mudanças.', defaultOn: true },
      { key: 'sessions', name: 'Iniciar sessões de refinamento', desc: 'Convida você pra resolver lacunas quando detecta gaps.', defaultOn: true },
      { key: 'block-publish', name: 'Bloquear publicações fora do tom', desc: 'Pode pausar conteúdo que diverge muito do brand kit.', defaultOn: false, danger: true },
      { key: 'web-research', name: 'Pesquisar concorrentes na web', desc: 'Mapeia referências e ângulos competitivos automaticamente.', defaultOn: true },
    ],
    preview: {
      label: 'Próxima análise da Vega',
      output: 'Detectei 3 posts da Lyra essa semana com coerência abaixo de 78%. Padrão: "para a empresa" em vez de "pra você" — desvio do bloco "Como você soa". Recomendação: reforçar bullet de linguagem direta no Brand Memory ou ajustar slider de voz da Lyra.',
      cost: 'haiku 4.5 · ~R$ 0,02',
    },
  },

  lyra: {
    key: 'lyra',
    name: 'Lyra',
    role: 'Redatora · Conteúdo',
    color: 'green',
    tagline: 'Escreve. Tudo. Posts, carrosséis, legendas, threads, copy de anúncio — Lyra é quem coloca palavra na tela.',
    bio: 'Lyra usa seu Brand Memory como bíblia. Lê voz, ICP, pilares e referências antes de cada post. Ela <strong>não improvisa</strong> — se uma decisão de marca não tá clara, ela puxa Vega antes de escrever. Rascunha rápido, refina se você pedir.',
    status: 'working',
    posts: '34 posts',
    avg: '86% coerência',
    model: 'Sonnet 4.6',
    modelFallback: 'Opus 4.7 em conteúdo crítico',
    sliders: [
      { key: 'voice', question: 'Voz: conservadora ou ousada?', labelLeft: 'Conservadora', labelRight: 'Ousada, opinativa', defaultValue: 75, explain: 'Lyra vai tomar posição em assuntos polêmicos do nicho. Defende ângulos contrários ao senso comum.' },
      { key: 'length', question: 'Tamanho médio dos posts', labelLeft: 'Curtos e diretos', labelRight: 'Longos e desenvolvidos', defaultValue: 45, explain: 'Mira na faixa de 600-1200 caracteres pra LinkedIn, ajusta sozinha pra Instagram.' },
      { key: 'hook', question: 'Tipo de gancho de abertura', labelLeft: 'Sutil e informativo', labelRight: 'Provocador e direto', defaultValue: 80, explain: 'Abre com afirmação polêmica ou estatística surpreendente. Risco: às vezes alienar parte da audiência.' },
    ],
    capabilities: [
      { key: 'web-data', name: 'Pesquisar dados na web', desc: 'Busca estatísticas e cases reais pra fundamentar posts.', defaultOn: true },
      { key: 'cite', name: 'Citar links e fontes', desc: 'Inclui referências quando relevante.', defaultOn: true },
      { key: 'use-examples', name: 'Usar exemplos do Brand Memory', desc: 'Calibra tom e estrutura pelos posts que deram certo.', defaultOn: true },
      { key: 'auto-publish', name: 'Publicar direto sem revisão', desc: 'Pula a Iris e manda direto pro feed.', defaultOn: false, danger: true },
    ],
    preview: {
      label: 'Como Lyra abriria o próximo post',
      output: 'Você montou seu Make.com em 2 horas e ele segue rodando 8 meses depois. Parece resiliente. Não é. Cada cenário é um single point of failure que ninguém entende — exceto você, no dia que você criou…',
      cost: 'sonnet 4.6 · ~R$ 0,12',
    },
  },

  iris: {
    key: 'iris',
    name: 'Iris',
    role: 'Revisora · Qualidade',
    color: 'yellow',
    tagline: 'Última camada antes de publicar. Compara cada post com seu Brand Memory e bloqueia o que diverge muito.',
    bio: 'Iris é o fiel da balança. Lê cada post da Lyra, cada imagem do Orion, e mede coerência com voz e tom. Se cai abaixo do mínimo, ela <strong>devolve com nota</strong>: "está fora da voz, refazer". Quando tudo bate, libera direto.',
    status: 'idle',
    posts: '89 revisões',
    avg: '23% reprovação',
    model: 'Haiku 4.5',
    modelFallback: 'sempre Haiku — é validação rápida',
    sliders: [
      { key: 'rigor', question: 'Rigor da revisão', labelLeft: 'Permissiva', labelRight: 'Exigente', defaultValue: 65, explain: 'Reprova posts com coerência abaixo de 75%. Pra mais consistência, sobe pra 80%+.' },
      { key: 'focus', question: 'Foco principal', labelLeft: 'Tom de voz e estilo', labelRight: 'Precisão factual', defaultValue: 40, explain: 'Prioriza voz e estilo, mas verifica fatos óbvios.' },
    ],
    capabilities: [
      { key: 'block', name: 'Bloquear publicação', desc: 'Pode pausar posts que falham no check.', defaultOn: true },
      { key: 'rewrite-request', name: 'Pedir reescrita à Lyra', desc: 'Devolve com nota explicando o que ajustar.', defaultOn: true },
      { key: 'auto-approve', name: 'Aprovar automaticamente acima de 90%', desc: 'Coerência alta = passa direto sem te avisar.', defaultOn: true },
      { key: 'skip-urgent', name: 'Pular validação em jobs urgentes', desc: 'Posts marcados "urgente" não passam por ela.', defaultOn: false, danger: true },
    ],
    preview: {
      label: 'Última nota da Iris',
      output: 'Post #34 reprovado · 67% coerência. Problema: 4 ocorrências de "a empresa pode" — voz da marca usa "você pode" sempre. 1 termo corporativo detectado. Devolvendo pra Lyra reescrever.',
      cost: 'haiku 4.5 · ~R$ 0,01',
    },
  },

  orion: {
    key: 'orion',
    name: 'Orion',
    role: 'Visual · Imagens',
    color: 'purple',
    tagline: 'Gera as imagens. Carrosséis, capas, ilustrações — Orion usa seu brand kit visual pra manter tudo na mesma família estética.',
    bio: 'Orion é o caçador de referências do time. Lê cores, fontes e imagens do Brand Memory e cria visuais fiéis. <strong>Mantém cache</strong> — se você pediu imagem parecida antes, reusa em vez de gerar de novo, economizando custo.',
    status: 'idle',
    posts: '28 imagens',
    avg: 'R$ 0,18 / img',
    model: 'Gemini Flash',
    modelFallback: 'sempre Gemini — melhor custo-benefício',
    sliders: [
      { key: 'style', question: 'Estilo visual base', labelLeft: 'Minimalista, clean', labelRight: 'Detalhado, denso', defaultValue: 30, explain: 'Estética enxuta, com bastante respiro — combina com voz técnica da marca.' },
      { key: 'palette-fidelity', question: 'Fidelidade à paleta', labelLeft: 'Restrita à marca', labelRight: 'Permite experimentar', defaultValue: 25, explain: 'Quase sempre #080808 + #F97316. Variações pontuais quando o tema pede.' },
    ],
    capabilities: [
      { key: 'generate', name: 'Gerar imagens com IA', desc: 'Cria visuais novos a partir de briefing.', defaultOn: true },
      { key: 'use-refs', name: 'Usar referências visuais do Brand Memory', desc: 'Imita estilo dos posts que deram certo.', defaultOn: true },
      { key: 'cache', name: 'Reusar imagens do cache', desc: 'Evita regerar quando o briefing é parecido — economiza custo.', defaultOn: true },
      { key: 'auto-logo', name: 'Aplicar logo automaticamente', desc: 'Coloca seu logo no canto inferior direito.', defaultOn: false },
    ],
    preview: {
      label: 'Próxima imagem que Orion vai gerar',
      output: 'Brief: capa de carrossel sobre Make.com. Estilo minimalista (slider 30%), paleta restrita #080808 + #F97316. Cache hit: 0% — gera nova. Estimado R$ 0,18.',
      cost: 'gemini · R$ 0,18',
    },
  },
};

export const AGENT_ORDER: AgentKey[] = ['lia', 'vega', 'lyra', 'iris', 'orion'];
```

## Handoffs entre agentes

Crie `frontend/src/data/handoffs.ts`:

```typescript
import type { AgentKey } from './types';

export interface Handoff {
  from: AgentKey;
  to: AgentKey;
  rule: string; // suporta **bold**
  trigger: string;
}

export const HANDOFFS: Handoff[] = [
  { from: 'lia', to: 'vega', rule: 'Quando você pede algo que **mexe na marca** (mudança de posicionamento, novo pilar, ajuste de voz), Lia chama Vega antes de qualquer agente produzir conteúdo.', trigger: 'palavra-chave: "marca", "posicionamento", "voz"' },
  { from: 'lia', to: 'lyra', rule: 'Job de **conteúdo escrito** (post, carrossel, copy) Lia distribui pra Lyra com o Brand Memory no contexto.', trigger: 'tipo: post · carrossel · copy' },
  { from: 'lyra', to: 'orion', rule: 'Quando o post pede imagem (carrossel, capa), Lyra escreve briefing visual e passa pra Orion.', trigger: 'output da Lyra contém slot de imagem' },
  { from: 'lyra', to: 'iris', rule: 'Todo post escrito **passa por Iris** antes de ir pro feed. Sem exceção (a menos que você desligue o capability).', trigger: 'sempre' },
  { from: 'iris', to: 'lyra', rule: 'Se Iris reprova (coerência < 75%), volta pra Lyra com nota. Máximo 2 idas e voltas — depois Lia escala pra você.', trigger: 'coerência abaixo do threshold' },
];
```

## Cores dos agentes (gradients)

Crie helpers em `frontend/src/lib/agent-colors.ts`:

```typescript
import type { AgentColor } from '@/data/types';

export const AGENT_GRADIENTS: Record<AgentColor, string> = {
  mixed:  'linear-gradient(140deg, #fb923c 0%, #f97316 50%, #60a5fa 100%)', // Lia
  orange: 'linear-gradient(140deg, #fb923c, #ea580c)',                       // Vega
  green:  'linear-gradient(140deg, #86efac, #22c55e)',                       // Lyra
  yellow: 'linear-gradient(140deg, #fde047, #eab308)',                       // Iris
  purple: 'linear-gradient(140deg, #d8b4fe, #a855f7)',                       // Orion
};

export const AGENT_BANNER_GRADIENTS: Record<AgentColor, string> = {
  mixed:  'radial-gradient(ellipse at top left, rgba(249, 115, 22, 0.45), transparent 50%), radial-gradient(ellipse at top right, rgba(96, 165, 250, 0.30), transparent 60%)',
  orange: 'radial-gradient(ellipse at top left, rgba(249, 115, 22, 0.45), transparent 70%)',
  green:  'radial-gradient(ellipse at top left, rgba(74, 222, 128, 0.45), transparent 70%)',
  yellow: 'radial-gradient(ellipse at top left, rgba(251, 191, 36, 0.45), transparent 70%)',
  purple: 'radial-gradient(ellipse at top left, rgba(192, 132, 252, 0.45), transparent 70%)',
};

export function getAgentGradient(color: AgentColor): string {
  return AGENT_GRADIENTS[color];
}

export function getAgentBannerGradient(color: AgentColor): string {
  return AGENT_BANNER_GRADIENTS[color];
}
```

Atualize o `<Avatar />` (criado no PROMPT 01) pra aceitar prop `agentKey: AgentKey` e usar `getAgentGradient(AGENTS[agentKey].color)` automaticamente.

## Critérios de aceite

- [ ] `frontend/src/data/types.ts` com tipos completos
- [ ] `frontend/src/data/agents.ts` com os 5 personagens (Lia, Vega, Lyra, Iris, Orion)
- [ ] `frontend/src/data/handoffs.ts` com 5 regras de handoff
- [ ] `frontend/src/lib/agent-colors.ts` com helpers de gradient
- [ ] Componente `<Avatar />` consome esses dados via `agentKey` prop
- [ ] Página `/_design` atualizada mostrando os 5 avatars com gradients corretos lado a lado pra validação visual

## Ao terminar, responda

Liste arquivos criados e diga: "Personagens dos agentes prontos. Aguardando PROMPT 03 com fluxos e telas."
