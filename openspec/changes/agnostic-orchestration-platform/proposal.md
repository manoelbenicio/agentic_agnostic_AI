# Proposal — Agnostic Orchestration Platform

## Why

Hoje a orquestração de múltiplos agentes de IA é feita com ferramentas que cobrem
apenas **uma camada** do problema:

- **Herdr** resolve a camada de execução (multiplexer de terminal, panes, estado do agente) — mas é single-user, sem tenancy, billing ou FinOps.
- **HerdMaster** (nosso control plane Python, já funcional) resolve dispatch, fila, ACL, watchdog e observabilidade — mas acoplado ao Herdr e sem produto/FinOps.
- **amux / Multica / OMA** provam padrões isolados (claim atômico, daemon, kanban, goal→DAG) mas nenhum entrega a camada de **produto enterprise** (multi-tenant, OAuth, FinOps, observabilidade Fortune-500) sobre uma execução **agnóstica e plugável**.

Nenhuma ferramenta ocupa o espaço de uma **Plataforma Enterprise Agnóstica de Orquestração de Agentes** que: (1) orquestre **CLIs de agente** (Codex, Kiro, Antigravity, Gemini, etc.) com **autenticação por assinatura/seat própria**, (2) ofereça **dois modos de operação por tarefa** (terminal/multiplexer ou socket/control-plane), (3) extraia performance máxima via um **Tech-Lead** que faz fan-out de subagentes, (4) tenha **FinOps + observabilidade enterprise**, e (5) permita ao cliente **montar squads visualmente** num canvas drag-and-drop.

Esta change captura essa plataforma, **reutilizando HerdMaster + Herdr (Opção C)** como base de execução/controle já provada, e construindo as camadas de produto que faltam — num **scaffold novo e limpo**, sem reaproveitar documentação ou código pela metade.

> **Nota explícita sobre LLM:** o núcleo **NÃO** usa um "LLM router" (litellm) próprio. Os agentes CLI já trazem o modelo embutido via assinatura. Roteamento por API de modelo fica como **módulo opcional secundário** (somente para clientes que queiram billing por token), nunca como motor principal.

## What Changes

- **[NEW]** Plataforma web nova em scaffold limpo e apartado (sem reaproveitar `AgnosticAI_Platform/`, `agnostic-ai-platform` change, nem `AgentVerse`).
- **[NEW]** **Dual Operation Mode por tarefa**: o usuário define, por tarefa, se ela roda em modo **Terminal** (multiplexer Herdr/tmux) ou em modo **Socket** (control plane FastAPI + kanban).
- **[NEW]** **Agent Runtime Adapter** — a costura agnóstica: uma interface única (`spawn/send/readState/stop/restore/meter`) por trás da qual cada vendor de CLI é um adapter (Codex, Kiro, Antigravity, Gemini, Cursor, …).
- **[NEW]** **Seat Pool + Isolamento de Credencial**: pool de seats por tenant/vendor, cada agente recebe um seat isolado (HOME/config-dir/env próprios) — modelo já validado no fork Herdr do cliente. Subagentes herdam o seat do agente-pai.
- **[NEW]** **Tech-Lead Orchestration**: um seat de agente atuando como coordenador, com autonomia para decompor objetivo e fazer **fan-out** (em média 2–3 subagentes por agente), sob admission control.
- **[NEW]** **Quota-Aware Scheduler**: escalonador ciente de quota/burn compartilhado por assinatura (caps 5h/semanal), com backoff em 429/503 e limite de concorrência.
- **[NEW]** **FinOps Dual Engine**: dois motores de custo — (a) por token (modo API) e (b) por utilização de seat (assinatura flat). Atribuição `tenant → projeto → issue → agente → runtime`. Pay-as-you-go ou mensal.
- **[NEW]** **Visual Squad Builder**: canvas drag-and-drop (`@xyflow/react`) onde o cliente monta squads como building blocks (ex.: 2 Codex + 2 Antigravity + 5 Gemini) e conecta agentes arrastando linhas, com transições visuais fluidas e sem lag.
- **[NEW]** **Observabilidade + Tracing E2E enterprise**: um trace que atravessa L4→L3→L2→L1 (issue → DAG → dispatch → sessão/PTY → custo → transcript), com gravação de sessão como artefato de troubleshooting.
- **[NEW]** **Multi-tenant + OAuth/Device-Auth** por seat, sem sobrescrever sessões (modelo validado no Herdr customizado).
- **[REUSE]** **HerdMaster** (control plane) e **Herdr** (execução) como dependências de runtime (Opção C).
- **[REFERENCE]** Design system OKLCH e capabilities de UI do Multica (issue-tracker, projects, skills, settings, inbox, search) como **referência visual/funcional** — reconstruídas limpas em Next.js.

## Capabilities

### New Capabilities

- `dual-operation-mode`: Seleção por tarefa entre execução Terminal (multiplexer) e Socket (control plane); roteamento do executor no dispatch.
- `agent-runtime-adapter`: Interface agnóstica de runtime de agente; adapters nativos por vendor com fallback de detecção de estado por screen-scrape.
- `seat-pool-credential-isolation`: Pool de seats por tenant/vendor com isolamento de credencial por processo e leasing com afinidade; subagentes herdam o seat do pai.
- `tech-lead-orchestration`: Coordenador (seat) que decompõe objetivo e faz fan-out de subagentes sob níveis de autonomia configuráveis.
- `quota-aware-scheduler`: Admission control e fila ciente de quota/burn por assinatura, com backoff 429/503 e teto de concorrência.
- `finops-dual-engine`: Motor duplo de custo (token vs seat) com atribuição hierárquica e modos pay-as-you-go/mensal.
- `visual-squad-builder`: Canvas drag-and-drop de composição de squads e topologia de conexões, com performance sem lag.
- `communication-topology-acl`: Definição granular de quem-fala-com-quem por squad/projeto, com topologia padrão hub-and-spoke (Tech-Lead autoridade central; agentes não falam entre si sem concessão explícita do TL), imposta em runtime.
- `dynamic-agent-registry`: Registro dinâmico de agentes com fonte única de verdade — add/remove em uma ação propaga automaticamente para allowlist, ACL e observabilidade, sem edição manual multi-arquivo; identidade estável apesar de churn de pane.
- `parallel-execution-governance`: Paralelismo máximo com isolamento (worktrees/path-guards) para um agente não quebrar o código do outro; ledger de check-in/out em disco (timestamp + agente) e evidência obrigatória em toda entrega de task.
- `observability-tracing`: Tracing E2E multi-camada, métricas, logs estruturados e gravação de sessão para deep-dive.
- `multi-tenant-identity`: Tenancy, RBAC e autenticação OAuth/Device-Auth por seat sem colisão de sessão.

### Reused / Referenced

- **Runtime reuse:** `HerdMaster` (dispatch, queue, ACL, watchdog, bus, DB) + `Herdr` (panes, socket API, state detection).
- **UI reference:** capabilities de UI do Multica (issue-tracker, issue-detail, projects-manager, skills-system, settings-workspace, inbox-notifications, my-issues-view, search-command-palette, design-system-oklch) — reconstruídas em scaffold limpo.

## Impact

- **Codebase:** scaffold novo e isolado (a definir o diretório na fase de implementação). Zero reaproveitamento de docs/código pela metade.
- **Runtime base:** HerdMaster (Python) + Herdr — Opção C. MVP estimado ~70–110 dias (calibrar com tamanho de time).
- **Stack:** Frontend **Next.js** (App Router) + Tailwind + shadcn/ui + `@xyflow/react` (canvas). Control plane **FastAPI** (Python). Persistência conforme HerdMaster (SQLite → Postgres na escala). Observabilidade Prometheus/Grafana/Alertmanager/Blackbox (já existente no HerdMaster).
- **Ambiente:** local-first em WSL/PowerShell, Docker quando necessário. Hardware alvo de dev: i9 / 20 cores / 64GB.
- **Auth:** OAuth/Device-Auth por seat, multi-subscrição do mesmo vendor sem sobrescrever sessão.
- **Sem LLM próprio no núcleo:** Tech-Lead é um seat; roteamento por API é módulo opcional futuro.
