# Design — Agnostic Orchestration Platform

## Context

Plataforma Enterprise Agnóstica de Orquestração de Agentes, construída sobre base
**reutilizada** (Opção C): `HerdMaster` (control plane Python, v1.0.0 funcional com
dispatch/queue/ACL/watchdog/bus/DB/observabilidade) + `Herdr` (multiplexer de
terminal, socket API local, detecção de estado de agente). As camadas de produto
(tenancy, FinOps, canvas, tracing E2E) são novas e limpas.

Decisões já travadas com o stakeholder durante a fase de exploração:
- Produto único (AgentVerse foi descartado; nunca foi para frente).
- Frontend Next.js (canvas `@xyflow/react` roda dentro do Next.js).
- **Sem LLM router (litellm) no núcleo** — agentes CLI trazem o modelo via seat.
- Reuso de HerdMaster + Herdr (Opção C).
- Modo de operação **definido por tarefa** pelo usuário.
- Subagentes **herdam o seat do agente-pai** (temporários, morrem rápido).

## Goals / Non-Goals

**Goals**
- Orquestrar CLIs de agente de forma agnóstica via uma interface de runtime única.
- Dois modos de operação por tarefa: Terminal (multiplexer) e Socket (control plane/kanban).
- Pool de seats com isolamento de credencial por processo; multi-subscrição do mesmo vendor.
- Tech-Lead (seat coordenador) com fan-out de 2–3 subagentes, sob admission control.
- Scheduler ciente de quota/burn (caps 5h/semanal) com backoff 429/503.
- FinOps dual (token vs seat) com atribuição hierárquica e modos pay-as-you-go/mensal.
- Visual Squad Builder drag-and-drop fluido (xyflow), reusando o design system OKLCH do Multica.
- Observabilidade/tracing E2E nível Fortune-500, com gravação de sessão.
- Multi-tenant + OAuth/Device-Auth por seat sem colisão de sessão.

**Non-Goals**
- LLM router próprio (litellm) no núcleo — adiado como módulo opcional.
- Reaproveitar código/docs pela metade (agnostic-ai-platform, AgnosticAI_Platform/src, AgentVerse).
- App desktop nativo (Electron) na v1 — web-first.
- Execução exclusivamente em nuvem na v1 — alvo primário é local-first (WSL/PowerShell/Docker).

## Decisions

### D1 — Reuso de HerdMaster + Herdr (Opção C)
Reutilizar o control plane HerdMaster (Python) e o multiplexer Herdr como base de
runtime. **Rationale:** ambos funcionam e têm testes; refazer multiplexer maduro
(Rust) seria ~200+ dias de desperdício. **Trade-off:** herdamos o acoplamento
Herdr↔HerdMaster (ADR-001); aceitável na fase atual.

### D2 — Frontend Next.js + Tailwind + shadcn/ui + @xyflow/react
Stack idêntica ao Multica para copy-paste de alta fidelidade do design system OKLCH;
canvas node-based via `@xyflow/react` embutido no Next.js. **Alternativa descartada:**
Vite+React (AgentVerse morto; sem ganho real).

### D3 — Núcleo SEM LLM router
Tech-Lead é um **seat de agente** atuando como coordenador, não uma chamada de API.
**Rationale:** mantém modelo seat-based puro, zero api-key, mais barato e 100% agnóstico.
Roteamento por API de modelo = módulo opcional futuro.

### D4 — Contrato único de Task/Evento → dois Executores
Um envelope tipado (`task_id, tenant, project, assignee_runtime, prompt, budget,
credential_ref, callbacks`) é despachado para **um de dois Executores** atrás da mesma
interface: `TerminalExecutor` (Herdr) e `SocketExecutor` (control plane/kanban). O modo
é escolhido **por tarefa**.

### D5 — Agent Runtime Adapter (costura agnóstica)
Interface `spawn/send/readState/stop/restore/meter`. Adapters nativos por vendor
fornecem detecção de estado confiável (o **moat**); fallback por screen-scrape quando
não houver adapter nativo.

### D6 — Seat Pool com isolamento por processo
Cada agente recebe um seat com HOME/config-dir/env isolados (modelo validado no fork
Herdr do cliente — login device-auth/OAuth sem sobrescrever sessão). Leasing com
afinidade (tarefas longas mantêm o seat). **Subagentes herdam o seat do pai** → pool
dimensionado pelo nº de agentes-pai, não de subagentes.

### D7 — Quota-Aware Scheduler
Admission control ciente de quota compartilhada por assinatura (caps 5h/semanal,
confirmados na pesquisa de vendor). Backoff exponencial em 429/503; teto de concorrência
(default alinhado ao `max-concurrent-tasks` do Multica ≈ 20).

### D8 — FinOps Dual Engine
Dois motores: (a) **token** (modo API) e (b) **seat-utilization** (assinatura flat —
pergunta vira "estou usando o que pago?"). Atribuição hierárquica `tenant→projeto→issue→agente→runtime`. Suporta pay-as-you-go e mensal.

### D9 — Observabilidade/Tracing E2E
Reusar stack do HerdMaster (Prometheus/Grafana/Alertmanager/Blackbox). Adicionar um
`trace_id` que atravessa L4→L3→L2→L1 e **gravação de sessão (PTY)** como artefato de
deep-dive.

### D10 — Local-first
Alvo primário: WSL/PowerShell + Docker quando necessário. Nuvem/multi-tenant gerenciado
é evolução posterior.

### D11 — Persistência unificada em Postgres
Migrar a persistência para **Postgres unificado** (plataforma + runtime HerdMaster), em vez
do híbrido com SQLite. **Rationale:** o stakeholder confirmou **problemas de lock recorrentes**
com o SQLite single-writer do HerdMaster sob concorrência de agentes — exatamente o hot path
do produto (dispatch, eventos de ciclo de vida, FinOps, audit log, streaming). Postgres dá
MVCC/escrita concorrente, multi-tenant (schemas/RLS), queries analíticas para FinOps e
particionamento para audit/tracing. **Evidência documentada:** TROUBLESHOOTING do HerdMaster
registra `database is locked` recorrente, `INC-P003` (WAL acumulando) e a necessidade de o
webhook de remediação **nunca** acessar o SQLite direto (só via HTTP API, pois o single-writer
travava). **Trade-off:** exige migração sqlite→postgres no HerdMaster.
**Sub-decisões em aberto:** `pgvector` (busca semântica/memória, como no Multica) fica adiado —
habilitado quando necessário.

### D12 — Redis desde o dia 1 (Docker local)
Incluir **Redis** desde o início como container Docker (o ambiente WSL do stakeholder já tem
Docker). **Uso:** pub-sub para streaming WebSocket (painel live por agente) e coordenação de
fila/locks leves do scheduler. **Rationale:** sem fricção de infra no local-first e já resolve o
broadcast de eventos quando houver múltiplas réplicas do control plane. **Trade-off:** mais um
serviço no compose — aceitável dado Docker disponível.

## Architecture

```
   USER ─► L4 CONTROL PLANE (FastAPI, multi-tenant)
            ├─ Identity & Seat Vault   ├─ FinOps Dual Engine   ├─ Observability + Audit
            ▼ (contrato único de task/evento — D4)
        L3 ORCHESTRATION BRAIN
            Tech-Lead (seat): objetivo→plano, fan-out 2–3 subagentes, admission control
            ▼ dispatch(task) — agnóstico de transporte
   ┌────────────────────────────┬────────────────────────────┐
   ▼ MODE A: TerminalExecutor    ▼ MODE B: SocketExecutor       (escolhido POR TAREFA — D4)
     (Herdr panes/socket)          (control plane + kanban)
   └──────────────┬─────────────┴──────────────┬─────────────┘
                  ▼ Agent Runtime Adapter (D5: spawn/send/readState/stop/restore/meter)
        codex · kiro · antigravity · gemini · cursor · …  (seats isolados — D6)
   ── REUSO (Opção C): HerdMaster (L2/L3 dispatch/queue/ACL/watchdog/obs) + Herdr (L1) ──
```

### D13 — Nada chumbado: tudo customizável pelo cliente
Princípio transversal: **nenhum valor crítico é hardcoded**. O cliente escolhe, por squad no
canvas, o seat do Tech-Lead, a topologia de comunicação, a composição de agentes e os modos de
operação. Defaults existem apenas como ponto de partida, sempre sobreescrevíveis.

### D14 — Registro dinâmico de agentes (resolve dor real)
O mapeamento de agentes hoje exige editar manualmente vários arquivos (allowlist em `config.toml`,
whitelist do webhook, observabilidade) a cada add/remove de pane — frágil e propenso a erro. A
plataforma adota **fonte única de verdade** com propagação automática (ACL/allowlist/observabilidade/
scheduler) e identidade interna estável desacoplada do ID de pane do Herdr.

### D15 — Governança de execução paralela
Paralelismo máximo com **isolamento obrigatório** (worktrees/path-guards) para um agente não
quebrar o código do outro; **ledger de check-in/out em disco** (timestamp+agente) e **evidência
obrigatória** em toda entrega — formalizando o protocolo já praticado no projeto.

### D16 — NLP/ChatOps adiado para Fase 3
A camada de linguagem natural (FEATURE-REQ-001 do HerdMaster / chatbot do builder) **não é
prioridade agora**; entra na Fase 3.

## HerdMaster Reuse Map (verificado em código/docs 2026-06-25)

Componentes já implementados e funcionais no HerdMaster — **reusados**, não reconstruídos:

| Camada / Capability | Já existe no HerdMaster | Trabalho NOVO sobre ele |
| --- | --- | --- |
| `agent-runtime-adapter` (Terminal) | `HerdrAdapter` (agent_list/pane_read/send/wait/spawn) | Generalizar p/ adapters nativos por vendor + estado semântico |
| `dual-operation-mode` (Socket) | TaskQueue (claim CAS) + DispatchInjector + HTTP API | Adicionar `TerminalExecutor` + roteador por-tarefa |
| `communication-topology-acl` | **AclEngine** (default-deny; roles orchestrator/worker/peer_reviewer/observer) | Editor visual (canvas→config) + concessão de edge lateral pelo TL |
| `tech-lead-orchestration` | Project Mode: planner + squad recommender + ETA + orchestrator role | Níveis de autonomia + fan-out de subagentes (no seat do pai) |
| `quota-aware-scheduler` | DispatchInjector backoff + retry/reassign | Awareness de quota/burn por assinatura (caps 5h/semanal) + 429/503 |
| `observability-tracing` | Prometheus/Grafana/Alertmanager/Blackbox + webhook remediation | `trace_id` E2E + rastreio por agente/runtime + gravação de sessão |
| MessageBus | JSON-RPC 2.0 (Unix socket, TTL, fallback, uni/broadcast/group) | Persistência em Postgres (D11) |
| Acoplamento Herdr↔HerdMaster | ADR-001 (soft coupling + reconexão, NFR-009) | Manter; expor estado de coupling na nova UI |

**Trabalho genuinamente novo (L4 + frontend):** multi-tenancy, seat pool + cofre de credencial,
FinOps dual engine, billing, Visual Squad Builder (Next.js + @xyflow/react), migração Postgres.

**Restrição de processo (GSD):** a execução deve seguir o Phase Loop GSD
(`Discuss → Plan → Execute → Verify → Ship`) conforme `GSD_MANDATORY_PROTOCOL.md`.

## Risks / Trade-offs

- **[R1: acoplamento Herdr↔HerdMaster (ADR-001)]** → manter adapter fino; isolar atrás do Agent Runtime Adapter para troca futura.
- **[R2: detecção de estado frágil (screen-scrape)]** → adapters nativos por vendor (moat); fallback scrape só quando necessário.
- **[R3: quota/burn compartilhado drena rápido]** → quota-aware scheduler + FinOps de utilização + alertas de burn-rate.
- **[R4: isolamento de credencial sob 20–30 processos]** → validar generalização do mecanismo do fork Herdr para todos os vendors e alta concorrência.
- **[R5: ToS de concorrência por seat]** → confirmar diretamente nos vendors antes de GA (pendente).
- **[R6: performance do canvas sob muitos nós]** → xyflow para squads típicos; avaliar canvas/WebGL só se escala exigir.

## Migration Plan

Projeto novo, sem estado legado a migrar. HerdMaster/Herdr entram como dependências de
runtime. Bootstrap local: subir HerdMaster + observabilidade (docker-compose já
existente), conectar o novo frontend Next.js + control plane, smoke test E2E.

## Open Questions

- **ToS de concorrência por seat** (OpenAI/Google) — confirmar antes de GA.
- **Diretório do scaffold novo** — definir nome/local na fase de implementação.
- **Persistência** — RESOLVIDO (D11): Postgres unificado (plataforma + HerdMaster).
- **Redis** — RESOLVIDO (D12): incluído desde o dia 1 via Docker (pub-sub WebSocket + coordenação de fila).
- **pgvector** — em aberto: habilitar quando precisar de busca semântica/memória de agentes.

## Backlog / Diferidos (regra: ajuste novo → backlog ou em pleno voo)

> **STATUS 2026-06-26:** TODOS os fixes de backlog foram ZERADOS e verificados
> (FIX-MSG, FIX-HMTOKEN, FIX-DEPS, ENV-OPS, FIX-HEALTH, FIX-WD[falso alarme],
> FIX-TOPO-PG, FIX-AUDIT). Resta apenas o REPO-INIT (push). Fase 3 (NLP/ChatOps)
> permanece diferida por decisão de escopo.

> Decisão do stakeholder (2026-06-25): para acelerar, ajustes novos não bloqueiam — vão para o
> backlog ou são feitos em pleno voo durante a execução.

- **Fase 3:** NLP/ChatOps (D16) — chatbot do builder / `herdmaster ask`.
- **A confirmar (não bloqueia início):** ToS de concorrência por seat nos vendors (OpenAI/Google).
- **Quando precisar:** pgvector (memória/busca semântica); sticky sessions/escala multi-réplica.
- **Em pleno voo:** schema multi-tenant detalhado do Postgres; adapters nativos por vendor (incrementais).
- **Backlog (de F0-B):** declarar `psycopg[binary]` em `HerdMaster/pyproject.toml` (dependência foi instalada na .venv mas não pinada — `pipx install --force` limpo quebraria). Fix de 1 linha; baixo risco, alta importância p/ reprodutibilidade.
- **Backlog (de P1-D):** resolver 2 vulnerabilidades moderadas reportadas pelo `npm audit` no frontend (AOP/web) — avaliar `npm audit fix` sem quebrar build.
- **Backlog (de P3-1):** (a) executors do app usam `InMemoryQueueClient`/`LocalRuntimeAdapter` — substituir por HerdrAdapter real + fila do HerdMaster (endereçado por P3-3); (b) topology persistence usa repo in-memory — promover a Postgres; (c) provisionar dashboards Grafana/alertas Alertmanager (as-code) para as novas métricas FinOps/Tracing.
- **RESOLVIDO (FIX-WD):** o `psycopg.OperationalError` no watchdog era **transitório** (Postgres fora do ar no momento do report da `live-integration-test-herdr`), não bug — RCA confirmou 16 passed / 1 skipped, fixture Postgres já aplicada. Sem fix necessário.
- **Backlog (de P3-4 smoke E2E — overall PASSED):** (a) AOP ainda não tem endpoint público `send_message`/`handoff` em runtime — o bloqueio lateral foi provado aplicando o AclEngine à ACL efetiva de `/squads/{id}/topology`, mas falta o endpoint de mensageria ao vivo p/ enforcement em runtime; (b) HerdMaster :8080 exige bearer token — socket-mode usou fallback ADR-001 no smoke; adicionar cliente HerdMaster tokenizado; (c) `/health` ainda não expõe `coupling_status` (resolvido por FIX-HEALTH).
- **Módulo opcional de LLM router** — quando/se habilitar billing por token.
