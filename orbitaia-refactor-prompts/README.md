# Refatoração Frontend Orbitaia — Guia de Uso

Cinco prompts para refatorar o frontend do `assistente-social-midia` introduzindo a **Lia** como interface principal e melhorando UX/UI. Foram desenhados pra serem colados em sequência no **Claude Code CLI**, cada um focado em uma camada do app.

## Antes de começar

**1. Tenha Claude Code CLI instalado e autenticado:**

```bash
claude code login
```

**2. Navegue até o repositório:**

```bash
cd /home/sodre/www/orbita.ia/assistente-social-midia
```

**3. Crie um branch dedicado pra refatoração:**

```bash
git checkout -b refactor/lia-and-ux-overhaul
```

**4. Tenha esses 5 arquivos `.md` salvos em algum lugar acessível** (pode ser `~/refactor-prompts/` ou similar). Eles **não devem ir pro repositório** — são guia de implementação, não código.

## Como usar

Os prompts foram escritos pra serem colados **em sequência**, um de cada vez, em **conversas separadas do Claude Code** (ou na mesma conversa, dependendo do contexto disponível).

### Ordem obrigatória

1. **PROMPT_00_CONTEXTO.md** — Cole primeiro. Claude Code só vai responder "entendido". Esse prompt **não gera código** — só estabelece contexto e voz da marca.

2. **PROMPT_01_DESIGN_SYSTEM.md** — Cole depois do 00. Gera tokens CSS, configura Tailwind, instala shadcn, cria componentes base. **Valide visualmente em `/_design`** antes de seguir.

3. **PROMPT_02_AGENTES_E_COPY.md** — Define os 5 personagens (Lia, Vega, Lyra, Iris, Orion) como dados estruturados. Sem UI ainda — só dados em `frontend/src/data/`.

4. **PROMPT_03_FLUXOS_E_TELAS.md** — Implementa todas as 14 telas, roteamento, stores Zustand, mock backend MSW. **A maior parte do trabalho.** Pode levar mais tempo.

5. **PROMPT_04_LIA_BUBBLE.md** — Última camada. Implementa a bolha flutuante e side panel da Lia, com sugestões contextuais e ingestão de arquivos via chat.

### Quando usar conversas separadas vs. mesma conversa

**Conversas separadas** (recomendado se a janela de contexto encher):
- Comece nova conversa pra cada prompt
- Cole o PROMPT_00 no início de cada nova conversa pra restabelecer contexto
- Mais seguro, mais lento

**Mesma conversa** (se contexto cabe):
- Cole 00 → 01 → valide → 02 → valide → 03 → valide → 04
- Mais ágil mas pode perder fidelidade no fim

Se você for fazer tudo em uma conversa só, peça ao Claude Code pra rodar `/clear` antes do prompt 04 mantendo só o resumo do que foi feito.

## Validação entre etapas

Depois de cada prompt, **valide antes de seguir**:

- **Pós-01:** abra `/_design` e veja se todos os componentes renderizam com cores corretas
- **Pós-02:** veja `/_design` atualizado com 5 avatars dos agentes em gradients corretos
- **Pós-03:** navegue por todas as 14 rotas, veja se sidebar atualiza estado ativo, veja se MSW intercepta as chamadas (DevTools → Network → "from service worker")
- **Pós-04:** clique na bolha, mande mensagens, teste sugestões contextuais em cada tela, anexe arquivo

Se algo quebrar, **não tente corrigir manualmente** — peça pro Claude Code corrigir descrevendo o problema. Mais barato.

## Comandos úteis durante o processo

```bash
# Rodar dev server enquanto o Claude Code edita arquivos
cd frontend && npm run dev

# Ver mudanças em tempo real (em outro terminal)
git status

# Reverter se Claude Code quebrar tudo
git stash

# Validar tipos TypeScript
cd frontend && npx tsc --noEmit
```

## Critérios de "pronto"

A refatoração está completa quando:

1. ✓ Todas as 14 rotas funcionam sem erro de console
2. ✓ Bolha da Lia aparece em todas telas autenticadas, não em onboarding
3. ✓ Side panel da Lia abre/fecha com slide animation
4. ✓ Sugestões contextuais mudam por rota
5. ✓ Save bar persiste entre navegações
6. ✓ Mock backend (MSW) responde a todos os endpoints
7. ✓ Mobile (≤600px): drawer da sidebar funciona, panel da Lia ocupa 100%
8. ✓ Storybook NÃO necessário, mas `/_design` mostra todos componentes
9. ✓ TypeScript sem erros (`npx tsc --noEmit` passa)

## Próximos passos depois dessa refatoração

A refatoração entrega **frontend completo com mock backend**. Próximas etapas (separadas):

- **Conectar backend real:** trocar handlers MSW por `fetch()` real pros endpoints FastAPI existentes
- **Implementar Geração de Conteúdo:** tela `/generate` que ainda está como "soon" no sidebar
- **Implementar histórico de versões:** tela `/brand-memory/block/:key/history` com timeline e comparação
- **Persistência:** salvar config de agentes no Supabase via PATCH `/api/agents/:key/config`

---

**Boa sorte. Qualquer dúvida sobre os prompts em si, volte pra conversa onde eles foram gerados — eu tenho contexto pra ajustar.**
