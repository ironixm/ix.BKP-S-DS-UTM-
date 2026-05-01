#!/usr/bin/env bash
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │  Start()  – V1.0.0                                         │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║
# ║ ██ ▀ ████████ │ commit:f563b5b                                             │║
# ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ _docs/mopgled/project_template/_Start(▶︎)_.command         │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * V1.0.0 - [sem detalhes]                                  │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Ativa venv
VENV_PATH="$ROOT/.venv"
ACTIVATE="$VENV_PATH/bin/activate"
if [[ -f "$ACTIVATE" ]]; then
  # shellcheck disable=SC1091
  source "$ACTIVATE"
else
  echo "⚠️ .venv não encontrado em $VENV_PATH"
  echo "   Crie com: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

PY="$VENV_PATH/bin/python"
[[ ! -x "$PY" && -n "${VIRTUAL_ENV:-}" ]] && PY="$VIRTUAL_ENV/bin/python"
[[ ! -x "$PY" ]] && PY="$(command -v python3)"

# Defaults simples
export PORT=${PORT:-11011}
export USE_RELOADER=${USE_RELOADER:-1}
export FLASK_DEBUG=${FLASK_DEBUG:-1}
export RENDER=${RENDER:-0}

# Libera porta se ocupada
if command -v lsof &>/dev/null; then
  PIDS=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
  if [[ -n "${PIDS:-}" ]]; then
    echo "🔪 Limpando porta $PORT ($PIDS)"
    kill -9 $PIDS 2>/dev/null || true
  fi
fi

echo "🚀 DEV simples — porta $PORT (reloader=${USE_RELOADER})"

OPEN_URL="http://localhost:${PORT}/"
HEALTH_URL_1="http://127.0.0.1:${PORT}/health"
HEALTH_URL_2="http://localhost:${PORT}/health"

open_or_focus_url() {
  local url="$1"
  # Tenta Google Chrome
  if command -v osascript &>/dev/null; then
    osascript >/dev/null 2>&1 <<OSA || true
try
  tell application "Google Chrome"
    set theURL to "$url"
    set found to false
    set localhostPrefix to "http://localhost:${PORT}"
    set loopbackPrefix to "http://127.0.0.1:${PORT}"
    repeat with w in windows
      repeat with t in tabs of w
        set u to URL of t
        if (u starts with theURL) or (u starts with localhostPrefix) or (u starts with loopbackPrefix) then
          set active tab index of w to (index of t)
          set index of w to 1
          set found to true
          exit repeat
        end if
      end repeat
      if found then exit repeat
    end repeat
    if not found then
      if (count of windows) is 0 then
        make new window
      end if
      tell window 1 to make new tab with properties {URL:theURL}
      set index of window 1 to 1
    end if
    activate
  end tell
end try
OSA
    if [[ $? -eq 0 ]]; then return 0; fi
    # Tenta Safari
    osascript >/dev/null 2>&1 <<OSA || true
try
  tell application "Safari"
    set theURL to "$url"
    set found to false
    set localhostPrefix to "http://localhost:${PORT}"
    set loopbackPrefix to "http://127.0.0.1:${PORT}"
    repeat with w in windows
      repeat with t in tabs of w
        set u to URL of t
        if (u starts with theURL) or (u starts with localhostPrefix) or (u starts with loopbackPrefix) then
          set current tab of w to t
          set found to true
          exit repeat
        end if
      end repeat
      if found then exit repeat
    end repeat
    if not found then
      if (count of windows) is 0 then
        make new document with properties {URL:theURL}
      else
        tell window 1 to set current tab to (make new tab with properties {URL:theURL})
      end if
    end if
    activate
  end tell
end try
OSA
    if [[ $? -eq 0 ]]; then return 0; fi
  fi
  # Fallback genérico
  if command -v open &>/dev/null; then
    open "$url" || true
  elif command -v xdg-open &>/dev/null; then
    xdg-open "$url" >/dev/null 2>&1 || true
  else
    "$PY" -m webbrowser "$url" || true
  fi
}

# Função: watcher de prontidão (foguete + focar aba) a cada start
run_ready_watcher() {
  (
    READY_TIMEOUT=${READY_TIMEOUT:-60}
    for i in $(seq 1 "$READY_TIMEOUT"); do
      if curl -fsS --max-time 1 "$HEALTH_URL_1" >/dev/null 2>&1 || \
         curl -fsS --max-time 1 "$HEALTH_URL_2" >/dev/null 2>&1; then
        # foguete (se disponível)
        if [[ -f "utils/foguete_azul.py" ]]; then
          "$PY" utils/foguete_azul.py --force --use-stdout --sound-file "static/sounds/foguete.wav" || true
        fi
        open_or_focus_url "$OPEN_URL"
        exit 0
      fi
      sleep 1
    done
  ) &
}

# Banner com dica de atalho
print_hotkeys_banner() {
  local cyan="\033[1;36m"; local reset="\033[0m"; local bold="\033[1m"; local magenta="\033[95m"
  echo -e "${magenta}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${reset}"
  echo -e "${cyan}💡 Dica:${reset} Pressione ${bold}R${reset} para ${bold}reiniciar${reset} o servidor • ${bold}P${reset} alterna Pushover • ${bold}T${reset} push teste • ${bold}Q${reset} para sair"
  echo -e "${magenta}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${reset}"
}

# Inicia/renicia o servidor Python em background
start_server() {
  export RELOADER_TYPE=${RELOADER_TYPE:-stat}
  "$PY" -u wsgi.py &
  CHILD=$!
  echo "🟢 Servidor iniciado (PID $CHILD) — aguardando /health…"
  run_ready_watcher
}

stop_server() {
  if kill -0 "$CHILD" >/dev/null 2>&1; then
    echo "🛑 Parando servidor (PID $CHILD)…"
    kill "$CHILD" >/dev/null 2>&1 || true
    for i in {1..10}; do
      if ! kill -0 "$CHILD" >/dev/null 2>&1; then break; fi
      sleep 0.3
    done
    if kill -0 "$CHILD" >/dev/null 2>&1; then
      echo "⚠️  Encerrando à força (SIGKILL)"
      kill -9 "$CHILD" >/dev/null 2>&1 || true
    fi
  fi
  if command -v lsof &>/dev/null; then
    PIDS=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
    if [[ -n "${PIDS:-}" ]]; then
      kill -9 $PIDS 2>/dev/null || true
    fi
  fi
}

trap_ctrl_c() {
  echo "\n👋 Saindo…"
  stop_server || true
  exit 0
}
trap trap_ctrl_c INT TERM

print_hotkeys_banner
start_server

while true; do
  if ! kill -0 "$CHILD" >/dev/null 2>&1; then
    echo "🔴 Servidor finalizado. Encerrando wrapper."
    wait "$CHILD" || true
    exit 0
  fi
  if IFS= read -rsn1 -t 1 key; then
    case "$key" in
      r|R)
        echo "\n🔁 Reiniciando servidor por comando do usuário (R)…"
        stop_server
        start_server
        ;;
      p|P)
        if [[ -f "_services/pushover/pushover.py" ]]; then
          STATUS="$("$PY" _services/pushover/pushover.py status 2>/dev/null || true)"
          TS="$(date +"%Y-%m-%d %H:%M:%S")"
          if echo "$STATUS" | grep -qi "ativo"; then
            echo "\n🔕 [$TS] Pausando Pushover (P)…"
            "$PY" _services/pushover/pushover.py disable || true
          else
            echo "\n🔔 [$TS] Ativando Pushover (P)…"
            "$PY" _services/pushover/pushover.py enable || true
          fi
        else
          echo "\n⚠️  Pushover não encontrado em _services/pushover"
        fi
        ;;
      t|T)
        if [[ -f "_services/pushover/pushover.py" ]]; then
          TS="$(date +"%Y-%m-%d %H:%M:%S")"
          echo "\n📣 [$TS] Enviando push de teste (T)…"
          "$PY" _services/pushover/pushover.py send --title "Pushover" --message "Teste de notificacao" --priority 0 || true
        else
          echo "\n⚠️  Pushover não encontrado em _services/pushover"
        fi
        ;;
      q|Q)
        echo "\n👋 Saindo por comando do usuário (Q)…"
        stop_server
        exit 0
        ;;
      *)
        :
        ;;
    esac
  fi
done

:
<<'EOF'
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
EOF
