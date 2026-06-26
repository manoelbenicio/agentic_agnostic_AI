#!/usr/bin/env bash
# =============================================================================
#  HerdMaster OPS Bootstrap
#  Arquivo: ops/bootstrap.sh
#  Projeto: Multi_Orchestration_Project_Tasks
#
#  USO:
#    bash bootstrap.sh <acao>
#
#  ACOES DISPONÍVEIS:
#    start         → Inicializa o HerdMaster (primeira vez ou após stop limpo)
#    stop          → Para o HerdMaster de forma ordenada
#    restart       → Para + Reinicia SEM apagar dados
#    reset-soft    → Para + Limpa tasks/prompts residuais + Reinicia (mantém DB)
#    reset-hard    → Para + Apaga DB completo + Reinicia do zero (IRREVERSÍVEL)
#    status        → Mostra estado atual de todos os componentes
#    agents-flush  → Envia /chat new para todos os panes dos agentes
#
#  FONTE DOS COMANDOS: código-fonte real lido em
#    /home/dataops-lab/.local/share/pipx/venvs/herdmaster/lib/python3.12/
#    site-packages/herdmaster/cli.py (verificado em 2026-06-25)
#
#  NUNCA executar sem autorização explícita do operador.
# =============================================================================

set -euo pipefail

# ─── Configuração ─────────────────────────────────────────────────────────────
HM_BIN="/home/dataops-lab/.local/bin/herdmaster"
HERDR_BIN="/home/dataops-lab/.local/bin/herdr"
HM_CONFIG_DIR="/home/dataops-lab/.config/herdmaster"
HM_PID_FILE="$HM_CONFIG_DIR/herdmaster.pid"
HM_DB="$HM_CONFIG_DIR/herdmaster.db"
HM_DB_WAL="$HM_CONFIG_DIR/herdmaster.db-wal"
HM_DB_SHM="$HM_CONFIG_DIR/herdmaster.db-shm"
HM_SOCK="$HM_CONFIG_DIR/herdmaster.sock"
HM_API_SOCK="$HM_CONFIG_DIR/herdmaster-api.sock"
HM_PROMPTS_DIR="$HM_CONFIG_DIR/prompts"

# Mapeamento pane → nome real do agente (label definido pelo operador, fonte: herdmaster.db)
# Atualizado em: 2026-06-25T14:50:15Z via SELECT id, label FROM agents (pós-flush + rename)
# Para atualizar: bash bootstrap.sh status (mostra os nomes atuais do DB)
declare -A AGENT_MAP=(
    # ── Squad_Snippers (workspace w6) ─────────────────────────────────────────────
    ["w6:p1"]="AGY_Opus-46"                 # Antigravity · Claude Opus 4.6 (Thinking) · worker
    ["w6:p2"]="AGY_Gemini_PRO-31"           # Antigravity · Gemini 3.1 Pro (High) · worker
    ["w6:p5"]="Codex_#1"                    # OpenAI Codex · gpt-5.5 medium · worker
    ["w6:p6"]="Codex_#2"                    # OpenAI Codex · gpt-5.5 medium · worker
    ["w6:p7"]="Kiro_Opus-48"               # Kiro CLI V3 · Claude Opus 4.8 High · orchestrator
    ["w6:p8"]="AGY_Flash35-High-Thinking"  # Antigravity · Gemini 3.5 Flash (High) · worker
)
# cli = CLI Operator (system/orchestrator) — sem pane Herdr, não incluído no flush de contexto
# Total: 7 agentes (6 panes + cli). Qualquer outro no DB = lixo de auto-registro, deletar.


# ─── Funções utilitárias ──────────────────────────────────────────────────────
log()  { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }
ok()   { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ✅ $*"; }
warn() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ⚠️  $*"; }
fail() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ❌ $*" >&2; exit 1; }

hm_is_running() {
    # Retorna 0 (true) se o processo HerdMaster está vivo
    if [ -f "$HM_PID_FILE" ]; then
        local pid
        pid=$(cat "$HM_PID_FILE")
        kill -0 "$pid" 2>/dev/null && return 0
    fi
    return 1
}

# ─── AÇÃO: status ─────────────────────────────────────────────────────────────
action_status() {
    log "=== STATUS DOS COMPONENTES ==="
    date -u

    echo ""
    log "--- HerdMaster Process ---"
    if hm_is_running; then
        local pid
        pid=$(cat "$HM_PID_FILE")
        ok "HerdMaster RUNNING | PID=$pid"
        ps -p "$pid" -o pid,etime,pcpu,pmem,cmd --no-header 2>/dev/null || true
    else
        warn "HerdMaster NOT RUNNING"
    fi

    echo ""
    log "--- Sockets ---"
    for sock in "$HM_SOCK" "$HM_API_SOCK"; do
        if [ -S "$sock" ]; then
            ok "Socket EXISTS: $sock ($(stat -c '%y' "$sock" 2>/dev/null | cut -d. -f1))"
        else
            warn "Socket MISSING: $sock"
        fi
    done

    echo ""
    log "--- Herdr Process ---"
    if pgrep -x herdr > /dev/null 2>&1; then
        ok "Herdr RUNNING (PID=$(pgrep -x herdr | head -1))"
        "$HERDR_BIN" workspace list 2>/dev/null | head -5 || true
    else
        warn "Herdr NOT RUNNING"
    fi

    echo ""
    log "--- Database ---"
    if [ -f "$HM_DB" ]; then
        ok "DB EXISTS: $HM_DB ($(du -h "$HM_DB" | cut -f1))"
        if [ -f "$HM_DB_WAL" ]; then
            log "  WAL: $(du -h "$HM_DB_WAL" | cut -f1)"
        fi
        # Task counts via Python (sqlite3 binary may not be installed)
        python3 -c "
import sqlite3
conn = sqlite3.connect('$HM_DB')
print('  Task counts:')
for row in conn.execute('SELECT state, COUNT(*) FROM tasks GROUP BY state ORDER BY 2 DESC'):
    print(f'    {row[0]:15} {row[1]}')
conn.close()
" 2>/dev/null || warn "  Could not read DB stats"
    else
        warn "DB NOT FOUND: $HM_DB"
    fi

    echo ""
    log "--- Agentes Registrados (DB) ---"
    python3 -c "
import sqlite3
conn = sqlite3.connect('$HM_DB')
for row in conn.execute('SELECT id, label, type, role, state, health, last_heartbeat FROM agents ORDER BY id'):
    pane, label, atype, role, state, health, hb = row
    print(f'  {label:30} | pane={pane:8} | type={atype:6} | state={state:8} | health={health:8} | hb={hb or \"nunca\"}')
conn.close()
" 2>/dev/null || warn "  Não foi possível ler agentes do DB"

    echo ""
    log "--- Prompt Files Residuais ---"
    local count
    count=$(find "$HM_PROMPTS_DIR" -name "task-*.md" 2>/dev/null | wc -l)
    log "  Arquivos task-*.md pendentes: $count"
}


# ─── AÇÃO: start ─────────────────────────────────────────────────────────────
action_start() {
    log "=== START: Inicializando HerdMaster ==="

    if hm_is_running; then
        warn "HerdMaster já está rodando (PID=$(cat "$HM_PID_FILE")). Use 'restart' se quiser reiniciar."
        exit 0
    fi

    if ! [ -f "$HM_DB" ]; then
        log "Banco de dados não encontrado — será criado automaticamente pelo HerdMaster."
    fi

    log "Iniciando HerdMaster em background (com HTTP API em :8080)..."
    nohup "$HM_BIN" start --http > "$HM_CONFIG_DIR/herdmaster-stdout.log" 2>&1 &


    log "Aguardando HerdMaster ficar pronto (até 15s)..."
    local attempts=0
    while [ $attempts -lt 15 ]; do
        sleep 1
        if hm_is_running; then
            ok "HerdMaster STARTED | PID=$(cat "$HM_PID_FILE")"
            sleep 2  # deixa o HM fazer sync inicial com o Herdr
            purge_unlisted_agents
            return 0
        fi

        attempts=$((attempts + 1))
    done

    fail "HerdMaster não iniciou em 15s. Verifique: $HM_CONFIG_DIR/herdmaster-stdout.log"
}

# ─── FUNÇÃO: purge de agentes não-documentados ───────────────────────────────
# Whitelist canônica: exatamente estes 7 agentes. Qualquer outro é lixo de auto-registro.
purge_unlisted_agents() {
    if ! [ -f "$HM_DB" ]; then return 0; fi
    local whitelist="('cli','w6:p1','w6:p2','w6:p5','w6:p6','w6:p7','w6:p8')"
    local deleted
    deleted=$(sqlite3 "$HM_DB" "DELETE FROM agents WHERE id NOT IN $whitelist; SELECT changes();")
    if [ "$deleted" -gt 0 ]; then
        warn "purge_unlisted_agents: $deleted agente(s) fora da whitelist removido(s) do DB"
    fi
}



# ─── AÇÃO: stop ───────────────────────────────────────────────────────────────
action_stop() {
    log "=== STOP: Parando HerdMaster ==="

    if ! hm_is_running; then
        warn "HerdMaster não está rodando."
        return 0
    fi

    local pid
    pid=$(cat "$HM_PID_FILE")
    log "Enviando SIGTERM ao PID $pid..."
    kill -SIGTERM "$pid" 2>/dev/null || true

    log "Aguardando shutdown gracioso (até 10s)..."
    local attempts=0
    while [ $attempts -lt 10 ]; do
        sleep 1
        if ! kill -0 "$pid" 2>/dev/null; then
            ok "HerdMaster STOPPED (PID $pid encerrado)"
            rm -f "$HM_PID_FILE" "$HM_SOCK" "$HM_API_SOCK"
            return 0
        fi
        attempts=$((attempts + 1))
    done

    warn "Processo não encerrou em 10s. Forçando SIGKILL..."
    kill -SIGKILL "$pid" 2>/dev/null || true
    sleep 1
    rm -f "$HM_PID_FILE" "$HM_SOCK" "$HM_API_SOCK"
    ok "HerdMaster KILLED (forçado)"
}

# ─── AÇÃO: agents-flush ───────────────────────────────────────────────────────
action_agents_flush() {
    log "=== AGENTS FLUSH: Enviando /chat new para todos os agentes ==="

    if ! pgrep -x herdr > /dev/null 2>&1; then
        fail "Herdr não está rodando. Não é possível enviar comandos aos panes."
    fi

    for pane in "${!AGENT_MAP[@]}"; do
        local agent_name="${AGENT_MAP[$pane]}"
        log "[$agent_name] pane=$pane → enviando /chat new..."
        "$HERDR_BIN" pane send "$pane" "/chat new" 2>/dev/null \
            && ok "  [$agent_name] /chat new enviado com sucesso" \
            || warn "  [$agent_name] falhou (pane $pane pode não existir no Herdr)"
        sleep 1
    done

    ok "Flush completo. Aguarde os agentes responderem antes de despachar novas tasks."
}

# ─── AÇÃO: restart ────────────────────────────────────────────────────────────
action_restart() {
    log "=== RESTART: Para + Reinicia (SEM apagar dados) ==="
    log "Dados preservados: DB, projetos, tasks, histórico"
    action_stop
    sleep 2
    action_start
    ok "Restart concluído. DB intacto."
}

# ─── AÇÃO: reset-soft ────────────────────────────────────────────────────────
action_reset_soft() {
    log "=== RESET SOFT: Para + Limpa resíduos + Reinicia ==="
    log "O que será APAGADO:"
    log "  - Prompt files residuais em $HM_PROMPTS_DIR/task-*.md"
    log "  - Sockets stale"
    log "O que será PRESERVADO:"
    log "  - Banco de dados (tasks, projetos, histórico)"
    log "  - Configuração (config.toml)"
    echo ""
    read -r -p "Confirmar reset-soft? [s/N] " confirm
    [[ "$confirm" =~ ^[sS]$ ]] || { log "Cancelado pelo operador."; exit 0; }

    action_stop
    sleep 1

    log "Limpando prompts residuais..."
    rm -f "$HM_PROMPTS_DIR"/task-*.md
    local removed=$?
    ok "Prompts limpos (exit=$removed)"

    log "Limpando sockets stale..."
    rm -f "$HM_SOCK" "$HM_API_SOCK" "$HM_PID_FILE"
    ok "Sockets removidos"

    sleep 1
    action_start

    log "Limpando contexto dos agentes no Herdr..."
    action_agents_flush

    ok "Reset soft completo."
}

# ─── AÇÃO: reset-hard ────────────────────────────────────────────────────────
action_reset_hard() {
    log "=== RESET HARD: Limpeza TOTAL — INÍCIO DO ZERO ==="
    warn "⚠️  ESTA AÇÃO É IRREVERSÍVEL"
    log "O que será PERMANENTEMENTE APAGADO:"
    log "  - Banco de dados completo: $HM_DB (todas as tasks, projetos, agentes)"
    log "  - WAL/SHM: $HM_DB_WAL / $HM_DB_SHM"
    log "  - Todos os prompt files em $HM_PROMPTS_DIR/"
    log "  - Todos os sockets e PID file"
    log "O que será PRESERVADO:"
    log "  - config.toml (configuração do sistema)"
    log "  - Processos Herdr e seus panes (apenas contexto será limpo via /chat new)"
    echo ""
    read -r -p "⚠️  CONFIRMAR RESET HARD? [Digite CONFIRMO para prosseguir] " confirm
    [[ "$confirm" == "CONFIRMO" ]] || { log "Cancelado. Reset hard NÃO executado."; exit 0; }

    log "Iniciando reset hard..."
    action_stop
    sleep 2

    log "Apagando banco de dados..."
    rm -f "$HM_DB" "$HM_DB_WAL" "$HM_DB_SHM"
    ok "DB apagado"

    log "Apagando prompts residuais..."
    rm -f "$HM_PROMPTS_DIR"/task-*.md
    ok "Prompts apagados"

    log "Apagando sockets e PID..."
    rm -f "$HM_SOCK" "$HM_API_SOCK" "$HM_PID_FILE"
    ok "Sockets e PID removidos"

    sleep 1

    log "Reiniciando HerdMaster (novo DB será criado automaticamente)..."
    action_start

    log "Limpando contexto de todos os agentes..."
    action_agents_flush

    ok "Reset hard concluído. Sistema está do zero."
    log "Próximo passo: criar um novo projeto com:"
    log "  herdmaster projects create 'Nome do Projeto' --scope 'Descrição do escopo'"
}

# ─── MAIN ─────────────────────────────────────────────────────────────────────
ACAO="${1:-}"

case "$ACAO" in
    start)        action_start ;;
    stop)         action_stop ;;
    restart)      action_restart ;;
    reset-soft)   action_reset_soft ;;
    reset-hard)   action_reset_hard ;;
    status)       action_status ;;
    agents-flush) action_agents_flush ;;
    *)
        echo ""
        echo "HerdMaster OPS Bootstrap"
        echo "Uso: bash bootstrap.sh <acao>"
        echo ""
        echo "Ações disponíveis:"
        echo "  status        → Estado atual de todos os componentes (sem alterar nada)"
        echo "  start         → Inicia o HerdMaster (primeira vez ou após stop limpo)"
        echo "  stop          → Para o HerdMaster de forma ordenada (SIGTERM → SIGKILL)"
        echo "  restart       → Para + Reinicia SEM apagar dados"
        echo "  agents-flush  → Envia /chat new para todos os panes (limpa contexto dos agentes)"
        echo "  reset-soft    → Para + Limpa prompts residuais/sockets + Reinicia (preserva DB)"
        echo "  reset-hard    → Para + Apaga DB completo + Reinicia do zero (IRREVERSÍVEL)"
        echo ""
        echo "Ordem recomendada para início do zero:"
        echo "  1. bash bootstrap.sh status          ← Diagnóstico primeiro"
        echo "  2. bash bootstrap.sh reset-hard      ← Se quiser limpar tudo"
        echo "  3. bash bootstrap.sh agents-flush    ← Limpar contexto dos agentes"
        echo "  4. herdmaster projects create ...    ← Criar novo projeto"
        echo ""
        exit 1
        ;;
esac
