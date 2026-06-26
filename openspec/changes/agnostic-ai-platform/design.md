## Context

O projeto AgnosticAI Platform é um produto proprietário construído do zero como substituto estratégico do Multica. O material de base está 100% disponível: 3 PRDs detalhados (PRD_AGENT1_CORE_FEATURES, PRD_AGENT2_CONFIG_SETTINGS, PRD_AGENT3_DESIGN_UX), design system completo extraído em OKLCH + tokens JSON, 70 screenshots do produto de referência, e o código-fonte do Multica clonado em `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/Mapeamento_New_Features/multica-src/`. O projeto existe isolado em `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/AgnosticAI_Platform/` com zero cross-pollution com outros projetos.

Stack confirmada do Multica (benchmark): Next.js App Router, Tailwind CSS, shadcn/ui (Radix), Lucide React, next-themes, i18next (en/zh/ko/ja), Auth por Email OTP + Google OAuth, WebSocket para agent streaming, React Server Components + Client.

## Goals / Non-Goals

**Goals:**
- Construir plataforma completa de gestão de agentes IA com OAuth Device Flow (eliminação total de API Keys)
- Roteamento agnóstico de LLM (OpenAI / Anthropic / Google Gemini) com billing centralizado
- Reproduzir e superar o design system OKLCH do Multica (Light/Dark mode, performance leve)
- Issue Tracker completo: 4 view modes, bulk actions, drag-and-drop Kanban
- Agent Working Live Panel com WebSocket streaming e Execution Logs em tempo real
- Skills System reutilizável com import de URL (ClawHub/Skills.sh/GitHub) e copy from runtime
- Settings em 10 tabs completos conforme PRD_AGENT2
- Inbox com 13 tipos de eventos, My Issues com scope tabs, Search global (Cmd+K)
- Stack de Observabilidade Day-2 integrada desde o primeiro commit
- 100% Docker-native — todos os serviços em containers

**Non-Goals:**
- Reutilizar código do Multica (usamos apenas como referência visual e funcional)
- Integrar com sistemas legados fora do ecossistema HerdMaster
- Suporte nativo a Lark/Feishu na v1 (pode ser adicionado como extensão futura)
- Aplicativo desktop nativo (Electron) — escopo é web-first; desktop wrapper é v2+

## Decisions

### D1 — Frontend: Next.js App Router + Tailwind + shadcn/ui
**Decisão:** Manter o mesmo stack do Multica para maximizar fidelidade de design e velocidade de desenvolvimento.
**Rationale:** shadcn/ui (Radix primitives) garante acessibilidade nativa. Next.js App Router com React Server Components otimiza performance. Tailwind CSS permite replicar o design system OKLCH com variáveis CSS customizadas.
**Alternativa descartada:** Vite + React (sem SSR nativo, pior SEO e performance inicial).
**SOURCE:** Stack confirmada por engenharia reversa do código-fonte Multica em `multica-src/`.

### D2 — Autenticação: OAuth Device Flow + JWT stateless
**Decisão:** OAuth Device Flow com polling backend; JWT para sessões stateless; zero API Keys expostas ao usuário.
**Rationale:** Elimina o maior detrator do Multica. Device Code flow (RFC 8628) é padrão para CLI/IoT/Desktop apps — o usuário nunca precisa copiar credenciais. Billing de LLM fica centralizado no backend.
**Alternativa descartada:** Email OTP (mantém fricção de volta ao e-mail); API Keys (o problema exato que estamos eliminando).
**DECISION LOG:**
```
DECISION: OAuth Device Flow (RFC 8628) para autenticação
SOURCE:   https://datatracker.ietf.org/doc/html/rfc8628
REF:      Section 3.1 — Device Authorization Request
RATIONALE: Padrão RFC, sem copiar/colar de credenciais, SSO Google/Microsoft
VERSION:  RFC 8628 (2019)
```

### D3 — Backend: FastAPI (Python) + PostgreSQL + Redis
**Decisão:** FastAPI async para API + PostgreSQL para persistência + Redis para sessions/cache/pub-sub WebSocket.
**Rationale:** FastAPI tem suporte nativo a async/await para WebSocket streaming (Agent Working Live Panel). PostgreSQL garante ACID para issues/projects/skills. Redis como pub-sub para broadcast de eventos de agentes em tempo real.
**Alternativa descartada:** Node.js backend (duplicidade de runtime com frontend; time tem mais proficiência em Python para LLM routing).

### D4 — LLM Router: Litellm como abstraction layer
**Decisão:** Usar `litellm` como proxy de roteamento agnóstico de LLM.
**Rationale:** Litellm tem suporte nativo a OpenAI, Anthropic, Google Gemini, Cohere, etc., com interface unificada. Permite troca de provider sem mudança de código no backend. Billing centralizado via `litellm.success_callback`.
**SOURCE:** https://docs.litellm.ai/docs/

### D5 — Real-time: WebSocket via FastAPI + Redis pub-sub
**Decisão:** FastAPI WebSocket endpoints + Redis pub-sub para broadcast de eventos de agentes.
**Rationale:** O Agent Working Live Panel exige streaming de baixa latência. Redis pub-sub permite múltiplas instâncias do backend broadcast para o frontend correto sem estado compartilhado em memória.

### D6 — Design System: OKLCH tokens em CSS variables
**Decisão:** Replicar exatamente o design system do Multica usando OKLCH CSS variables com Tailwind `@theme`.
**Rationale:** OKLCH garante uniformidade perceptual de cor em ambos os modos (light/dark). Os tokens já foram extraídos nos arquivos `design-tokens/colors-dark.json` e `colors-light.json`. Fontes: Inter (UI), Source Serif 4 (editorial), Geist Mono (código).

### D7 — Isolation: Git worktrees por sub-agente
**Decisão:** Cada sub-agente de desenvolvimento opera em um Git worktree isolado. Merge via PR após CI.
**Rationale:** Elimina risco de um sub-agente (ex: UI) sobrescrever código de outro (ex: OAuth backend). O orquestrador HerdMaster gerencia os worktrees e garante que o path-guard esteja ativo.

### D8 — Docker: Composição completa desde o dia 1
**Decisão:** `docker-compose.yml` com todos os serviços desde o primeiro commit (frontend, backend, postgres, redis, prometheus, grafana).
**Rationale:** Garante paridade entre ambientes de desenvolvimento e produção. Observabilidade Day-2 não é afterthought — é infraestrutura de base.

## Risks / Trade-offs

- **[Risk: Complexidade do OAuth Device Flow]** → Mitigation: Usar biblioteca `authlib` para FastAPI que implementa RFC 8628 nativamente; escrever mock do provider OAuth para testes locais sem dependência de Google/Microsoft.
- **[Risk: WebSocket + múltiplas réplicas do backend]** → Mitigation: Redis pub-sub como broker; sticky sessions via nginx upstream hash se necessário na v1.
- **[Risk: Fidelidade de design ao Multica]** → Mitigation: 70 screenshots + design-tokens JSON + componentes-catalog.md como referência visual permanente durante desenvolvimento.
- **[Risk: litellm versioning/breaking changes]** → Mitigation: Pinnar versão exata no `requirements.txt`; wrapper interno que abstrai chamadas litellm para facilitar eventual substituição.
- **[Risk: Sub-agente de UI quebrar código do sub-agente de Auth]** → Mitigation: Git worktrees obrigatórios + path-guard no CI; worktree de UI tem write-access apenas em `/AgnosticAI_Platform/src/app/` e `/components/`; worktree de Auth tem write-access apenas em `/AgnosticAI_Platform/src/api/auth/`.
- **[Risk: Escopo excessivo para v1]** → Mitigation: Priorização rigorosa — MVP é Auth + Issues + Projects + Observability. Skills/Settings/Inbox são features de v1.5 executadas em paralelo após fundação estável.

## Migration Plan

N/A — projeto novo sem estado legado para migrar. Deploy inicial:
1. `docker-compose up -d` no ambiente WSL
2. `alembic upgrade head` para migrations do PostgreSQL
3. Configurar OAuth provider (Google Cloud Console) com redirect URI local
4. Provisionar dashboards Grafana via JSON em `deploy/observability/grafana/dashboards/`
5. Smoke test via `/health` endpoints de todos os serviços

Rollback: `docker-compose down` — stateless por design na v1 (PostgreSQL é o único estado persistente).

## Open Questions

- **OAuth Provider em v1:** Usar apenas Google SSO ou incluir Microsoft desde o início? (Recomendação: Google first, Microsoft em v1.5)
- **i18n scope:** Multica suporta en/zh/ko/ja. Para v1, apenas `en` com estrutura i18next já configurada para expansão futura?
- **Lark/Feishu:** Excluído do Non-Goals. Confirmar se algum stakeholder precisa na v1.
- **Desktop app (Electron):** Confirmado como v2+? Afeta algumas decisões de CSP e deep-link OAuth.
