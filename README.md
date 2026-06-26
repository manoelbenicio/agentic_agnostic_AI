# Agnostic Orchestration Platform

Plataforma Enterprise Agnóstica de Orquestração de Agentes de IA — orquestra **CLIs de agente**
(Codex, Kiro, Antigravity, Gemini, …) com autenticação por assinatura/seat, dois modos de operação
por tarefa (terminal/multiplexer e socket/control-plane), Tech-Lead com fan-out, FinOps, observabilidade
e um Visual Squad Builder onde o cliente monta squads e define a topologia de comunicação.

## Arquitetura (resumo)

```
  L4 Produto      multi-tenant · OAuth/seat vault · FinOps dual · observabilidade
  L3 Cérebro      Tech-Lead (seat) · goal→plano · fan-out · quota-aware scheduler
  L2 Controle     contrato task/evento · dual executor (terminal/socket) · dispatch/queue
  L1 Execução     Agent Runtime Adapter · seats isolados · Herdr panes
```

Construído reutilizando **HerdMaster** (control plane Python) + **Herdr** (multiplexer), com o
control-plane FastAPI e o frontend Next.js sob `AOP/`.

## Componentes

- `AOP/control-plane/` — FastAPI (:8090): core, executors, registry, seats, topology, orchestrator,
  scheduler, finops, tracing, messaging, coupling, app.
- `AOP/web/` — frontend Next.js + Tailwind + shadcn/ui + @xyflow/react (Visual Squad Builder, dashboard, live trace).
- `AOP/deploy/` — docker-compose (Postgres + Redis).
- `AOP/ops/` — scripts de operação (start / stop / flush-restart).
- `AOP/e2e/` — smoke E2E.
- `HerdMaster/` — control plane reutilizado (dispatch, ACL, watchdog, bus, observabilidade).
- `openspec/` — especificação de referência (`changes/agnostic-orchestration-platform`).

## Subir o ambiente

```bash
bash AOP/ops/start.sh        # sobe Postgres, Redis, observabilidade, HerdMaster, control-plane, frontend
bash AOP/ops/stop.sh         # encerra os serviços (Herdr NÃO é tocado)
bash AOP/ops/flush-restart.sh # flush de logs/caches (+ DB com CONFIRMO) e restart
```

Serviços: Postgres :5432 · Redis :6379 · HerdMaster :8080 · Control-plane :8090 · Frontend :13000
· Observabilidade (Prometheus :9090 / Grafana :3000 / Alertmanager :9093).

## Status

Build inicial estável: fundação + control-plane integrado + frontend + acoplamento HerdMaster/Herdr,
smoke E2E **passou** (topologia hub-and-spoke com default-deny, dispatch terminal/socket, tracing por
agente/runtime, FinOps). Ver `AOP/e2e/REPORT.md`.
