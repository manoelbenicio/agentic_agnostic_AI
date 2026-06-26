## Why

O produto **Multica** (referência de mercado para orquestração de agentes IA) possui design e UX de excelência, mas o modelo de autenticação baseado em **API Keys por usuário** cria fricção extrema (5+ minutos de setup), custos descentralizados e incontroláveis, e risco de vazamento de credenciais. Nosso ecossistema HerdMaster/Herdr já validou o modelo superior de **OAuth Device Flow** — construiremos nossa própria plataforma proprietária, agnóstica de modelo LLM, retendo o nível de design do Multica e eliminando todos os seus detratores críticos.

## What Changes

- **[NEW]** Plataforma web completa de gestão de agentes IA (AgnosticAI Platform) construída do zero em `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/AgnosticAI_Platform/`
- **[NEW]** Sistema de autenticação via **OAuth Device Flow** (Google/Microsoft SSO) — elimina 100% das API Keys no lado do usuário
- **[NEW]** Roteamento agnóstico de LLM (OpenAI, Anthropic, Google Gemini) com billing centralizado no backend
- **[NEW]** Issue Tracker completo com List/Board/Gantt views, drag-and-drop Kanban, e sistema de status/prioridade (6 status SVG + 5 prioridades)
- **[NEW]** Issue Detail com Activity Timeline, Agent Working Live Panel (WebSocket), e Execution Logs em tempo real
- **[NEW]** Projects Manager com cards de progresso, scoped issue tracker por projeto
- **[NEW]** Skills System — biblioteca de habilidades reutilizáveis atribuíveis a agentes (create manual / import URL / copy from runtime)
- **[NEW]** Settings completo (10 tabs: General, Members, Repositories, GitHub, Integrations, Profile, Preferences, Notifications, API Tokens, Labs)
- **[NEW]** Inbox de notificações com 13 tipos de eventos e painel de detalhes resizável
- **[NEW]** My Issues — view pessoal filtrada por scope (All/Assigned/Created/My Agents)
- **[NEW]** Search global (Cmd+K / Ctrl+K) com command palette — issues, pages, commands, members
- **[NEW]** Design System OKLCH completo com Light/Dark mode, fontes Inter/Source Serif 4/Geist Mono
- **[NEW]** Stack de Observabilidade Day-2 integrada desde o primeiro commit (Prometheus + Grafana + Blackbox)
- **[NEW]** 100% Docker-native — frontend + backend + databases em containers
- **BREAKING** Autenticação: zero dependência de API Keys; modelo OAuth Device Flow mandatório

## Capabilities

### New Capabilities

- `auth-oauth-device-flow`: Fluxo completo de autenticação OAuth Device Login — device code, polling, JWT stateless, SSO Google/Microsoft. Elimina API Keys.
- `llm-agnostic-router`: Backend de roteamento de LLM agnóstico com suporte a OpenAI, Anthropic e Google Gemini. Billing centralizado, nenhuma credencial exposta ao usuário.
- `issue-tracker`: Sistema completo de Issues com 4 view modes (List, Board/Kanban, Swimlane, Gantt), filtros multi-dimensionais, bulk actions, right-click context menu.
- `issue-detail`: Página de detalhe de issue com Activity Timeline, Properties Sidebar, Agent Working Live Panel (WebSocket streaming), Execution Logs, e TipTap editor para descrição.
- `projects-manager`: Gestão de projetos com cards de progresso (completed/total issues), status tags (Active/Paused/Completed), project creation modal, scoped issue tracker.
- `skills-system`: Sistema de Skills reutilizáveis — criação manual, import de URL (ClawHub/Skills.sh/GitHub), copy from runtime com batch import e conflict resolution.
- `settings-workspace`: 10 abas de configuração: General (workspace name/slug/prefix/context), Members (invite/roles/permissions), Repositories (git URLs), GitHub (App OAuth integration), Integrations (Lark/Feishu bot binding), Profile, Preferences (theme/language/timezone), Notifications, API Tokens, Labs.
- `inbox-notifications`: Hub central de notificações com 13 tipos de eventos (assignments, status changes, agent activity, comments, etc.), read/unread states, bulk archive actions.
- `my-issues-view`: View pessoal filtrada com scope tabs (All/Assigned/Created/My Agents), 3 view modes, filtro rápido "Agents working", grouping por Status ou Assignee.
- `search-command-palette`: Busca global via Cmd+K com command palette (cmdk + Radix), debounce 300ms, AbortController, highlight de matches, navegação por teclado.
- `design-system-oklch`: Design system completo baseado em OKLCH — tokens light/dark mode, fontes Inter/Source Serif 4/Geist Mono, border-radius 10px/8px, spacing scale Tailwind, animações (pulse, ping, skeleton).
- `observability-stack`: Stack Day-2 — Prometheus `/metrics`, Grafana dashboards as code, Blackbox Exporter, alertas, integração desde o primeiro commit.
- `docker-infrastructure`: 100% Docker-native — todos os serviços (Next.js frontend, FastAPI backend, PostgreSQL, Redis) em containers com docker-compose.

### Modified Capabilities

<!-- Nenhuma especificação existente afetada — projeto novo isolado em AgnosticAI_Platform/ -->

## Impact

- **Codebase:** Todo código novo em `/mnt/c/VMs/Projects/Multi_Orchestration_Project_Tasks/AgnosticAI_Platform/` — zero cross-pollution com HerdMaster ou outros projetos
- **Stack:** Next.js App Router + Tailwind CSS + shadcn/ui (Radix) + Lucide React + FastAPI + PostgreSQL + Redis
- **Auth:** OAuth Device Flow substitui completamente API Keys — nenhum usuário final gerencia credenciais de LLM
- **Infra:** docker-compose com network isolation entre serviços; sub-agentes de desenvolvimento operam em Git worktrees isolados
- **Observabilidade:** Prometheus scrape + Grafana dashboards provisionados como código (JSON) no `deploy/observability/`
- **Documentação:** Todos os caminhos referenciados em formato WSL nativo (`/mnt/c/...`) para compatibilidade total com HerdMaster/Herdr
