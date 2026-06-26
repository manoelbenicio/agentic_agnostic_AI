# Tasks — Agnostic Orchestration Platform

> Base reutilizada (Opção C): HerdMaster (control plane) + Herdr (execução).
> Núcleo SEM LLM router. Frontend Next.js + @xyflow/react. Local-first (WSL/Docker).

## 1. Fundação & Scaffold Limpo
- [ ] 1.1 Definir e criar o diretório do scaffold novo e isolado (sem reusar AgnosticAI_Platform/ ou AgentVerse).
- [ ] 1.2 Bootstrap do control plane FastAPI (multi-tenant) com `/health`, `/health/ready`, `/metrics`.
- [ ] 1.3 Integrar HerdMaster como dependência de runtime (dispatch/queue/ACL/watchdog/bus/DB) atrás de uma fachada fina.
- [ ] 1.3a Migrar a persistência do HerdMaster de SQLite para **Postgres unificado** (D11) — elimina o gargalo single-writer/locks recorrentes.
- [ ] 1.3b Definir schema multi-tenant em Postgres (plataforma + runtime); RLS/schemas por tenant; adiar pgvector/Redis até necessário.
- [ ] 1.4 Integrar Herdr como executor de terminal via socket API (panes, send, read, wait, state).
- [ ] 1.5 docker-compose local (control plane + Postgres + Redis + observabilidade existente do HerdMaster).
- [ ] 1.6 Subir Redis (D12) para pub-sub do streaming WebSocket e coordenação de fila do scheduler.

## 2. Contrato Único de Task/Evento & Dual Operation Mode
- [ ] 2.1 Definir o envelope tipado de task (`task_id, tenant, project, assignee_runtime, prompt, budget, credential_ref, operation_mode, callbacks`).
- [ ] 2.2 Definir o stream de eventos de ciclo de vida normalizado (`queued/claimed/running/blocked/done/failed`).
- [ ] 2.3 Implementar `TerminalExecutor` (Herdr) atrás da interface de executor.
- [ ] 2.4 Implementar `SocketExecutor` (control plane + claim/poll) atrás da mesma interface.
- [ ] 2.5 Implementar roteamento por tarefa: `operation_mode` escolhido pelo usuário decide o executor.

## 3. Agent Runtime Adapter (costura agnóstica)
- [ ] 3.1 Definir interface `spawn/send/readState/stop/restore/meter`.
- [ ] 3.2 Implementar adapters nativos (Codex, Kiro, Antigravity, Gemini) com detecção de estado semântica.
- [ ] 3.3 Implementar fallback de detecção por screen-scrape (process name + output heuristics).
- [ ] 3.4 Implementar hook `meter` (tokens p/ API; seat-minutes p/ assinatura).

## 4. Seat Pool & Isolamento de Credencial
- [ ] 4.1 Implementar pool de seats por tenant/vendor com leasing e release.
- [ ] 4.2 Implementar sandbox de credencial por processo (HOME/config-dir/env isolados) — validar generalização do mecanismo do fork Herdr.
- [ ] 4.3 Implementar herança de seat por subagentes (não consomem seats extras do pool).
- [ ] 4.4 Implementar afinidade de lease + refresh/rotação de token em expiração.

## 5. Quota-Aware Scheduler
- [ ] 5.1 Rastrear quota/burn compartilhado por vendor (caps 5h/semanal).
- [ ] 5.2 Admission control: enfileira (não falha) quando quota esgota; teto de concorrência (~20).
- [ ] 5.3 Backoff exponencial com jitter em 429/503.
- [ ] 5.4 Forecasting de burn-rate + alerta via stack de observabilidade.

## 6. Tech-Lead Orchestration
- [ ] 6.1 Designar seat como Tech-Lead; decomposição de objetivo → plano.
- [ ] 6.2 Fan-out limitado (média 2–3 subagentes/agente) sob admission control.
- [ ] 6.3 Níveis de autonomia (0–4) com gate de aprovação humana quando exigido.

## 7. Communication Topology & ACL
- [ ] 7.1 Modelar topologia direcional (edges permitidas) por squad/projeto.
- [ ] 7.2 Implementar default hub-and-spoke (TL autoridade central; lateral negada por padrão).
- [ ] 7.3 Concessão/revogação explícita de edges laterais pelo Tech-Lead.
- [ ] 7.4 Enforcement em runtime de `send_message/handoff/assign` (bloqueio + auditoria) — sobre ACL/bus do HerdMaster.
- [ ] 7.5 Validação de topologia antes da ativação.

## 8. Visual Squad Builder (Next.js + @xyflow/react)
- [ ] 8.1 Canvas com nós de agente como building blocks (contagens por vendor).
- [ ] 8.2 Edição de topologia por linhas de conexão (alimenta a capability de ACL).
- [ ] 8.3 Performance fluida (drag/connect/pan/zoom) com transições visuais, sem lag.
- [ ] 8.4 Entry-point opcional de chatbot que propõe squad + topologia.

## 9. FinOps Dual Engine
- [ ] 9.1 Motor de custo por token (API) e por utilização de seat (assinatura).
- [ ] 9.2 Atribuição hierárquica `tenant→projeto→issue→agente→runtime`.
- [ ] 9.3 Detecção de seat ocioso + recomendação de right-sizing.
- [ ] 9.4 Modos de billing pay-as-you-go e mensal.

## 10. Multi-Tenant Identity & Auth
- [ ] 10.1 Isolamento multi-tenant de recursos.
- [ ] 10.2 Auth de seat via OAuth/device-auth, multi-subscrição do mesmo vendor sem colisão de sessão.
- [ ] 10.3 RBAC (admin/operator/viewer) + auditoria.

## 11. Observabilidade & Tracing E2E
- [ ] 11.1 Propagar `trace_id` por L4→L3→L2→L1.
- [ ] 11.2 Métricas/logs estruturados de agentes/seats/fila/quota (reuso Prometheus/Grafana/Alertmanager/Blackbox).
- [ ] 11.3 Gravação de sessão (PTY) como artefato consultável por `trace_id`.
- [ ] 11.3a Rastreabilidade isolada por agente E por runtime (timeline, chain-of-thought, tool calls, estado, burn individual) — filtrável por agente/runtime.
- [ ] 11.4 Audit log imutável (lease, violação de topologia, decisões de autonomia, billing).

## 12. UI da Plataforma (reconstrução limpa, design system Multica)
- [ ] 12.1 Design system OKLCH (light/dark, Inter/Source Serif/Geist Mono) em Next.js.
- [ ] 12.2 Issue tracker + kanban (modo socket) + projects manager.
- [x] 12.3 Painel live por agente (WebSocket): chain-of-thought, saúde, estado, burn de tokens.
- [ ] 12.4 Settings, inbox, my-issues, search (Cmd+K).

## 13. Validação E2E
- [ ] 13.1 Smoke E2E: criar squad no canvas → topologia → dispatch por tarefa (terminal e socket) → observabilidade → custo.
- [ ] 13.2 Confirmar ToS de concorrência por seat nos vendors (OpenAI/Google) antes de GA.
- [ ] 13.3 Teste de carga local (alvo: ~10 agentes-pai, fan-out 2–3) no hardware de dev (i9/20c/64GB).

## 14. Registro Dinâmico de Agentes (resolve a dor multi-arquivo)
- [ ] 14.1 Definir fonte única de verdade do registro de agentes (substitui allowlist em config.toml + whitelist do webhook + alvos de observabilidade).
- [ ] 14.2 Add/remove de agente em uma ação (API/UI/canvas) com propagação automática para ACL, allowlist, observabilidade e scheduler — zero edição manual de arquivos.
- [ ] 14.3 Auto-discovery com enrollment controlado (phantom de outro workspace ignorado por padrão; pane legítimo enrolado em 1 passo).
- [ ] 14.4 Identidade interna estável mapeada ao pane atual (sobrevive a churn/compactação de IDs do Herdr) — preserva histórico/custo/traces.

## 15. Governança de Execução Paralela
- [ ] 15.1 Isolamento por worktree/path-guard para paralelismo máximo sem um agente quebrar o código do outro.
- [ ] 15.2 Ledger de check-in/out em disco na pasta do projeto (append-only, UTC + nome do agente, arquivos a tocar / tocados, status).
- [ ] 15.3 Flag de violação para CHECK-IN sem CHECK-OUT após timeout.
- [ ] 15.4 Evidência obrigatória em toda entrega de task (print/arquivo/SHA-256/link); CHECK-OUT sem evidência = inválido.
- [ ] 15.5 Vincular evidência e ledger ao `trace_id` da task.
