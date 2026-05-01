#!/usr/bin/env bash
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │  Start()  – V3.2.0                             │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-16 - 14:10         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _Start(▶︎)_.command                            │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V3.2.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

# _Start(▶︎)_.command — ix.BLZ-S(DS+UTM)
# ix.WP V3.1.14 | Ir.On | ironix.com.br
# Self-contained: TUI embutida via heredoc (sem .py separado)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ── Timezone ────────────────────────────────────────────
export TZ="America/Sao_Paulo"

# ── Detectar ix.WP (bundle da extensão; fallback em _docs) ────────
IX_WP_DIR=""
for d in "$ROOT"/_docs/ix.WP-V*/; do
  [[ -d "$d" ]] && IX_WP_DIR="$d"
done
if [[ -z "${IX_WP_DIR:-}" ]]; then
  for d in "$HOME"/.vscode/extensions/ironix.ixwp-ext-*/bundle/ix.WP-V*/ "$HOME"/.cursor/extensions/ironix.ixwp-ext-*/bundle/ix.WP-V*/; do
    [[ -d "$d" ]] && IX_WP_DIR="$d"
  done
fi
IX_WP_DIR="${IX_WP_DIR%/}"

# ── TUI (ix_terminal / Textual): embutida neste script ─────────
_try_tui() {
  local py3
  py3="$(command -v python3 2>/dev/null || true)"
  [[ -z "$py3" ]] && return 1
  "$py3" -c "import textual" 2>/dev/null || {
    echo "📦 Instalando textual..."
    "$py3" -m pip install --quiet textual 2>/dev/null || return 1
    "$py3" -c "import textual" 2>/dev/null || return 1
  }
  if [[ -n "${IX_WP_DIR:-}" ]]; then
    local ix_mod="$IX_WP_DIR/1-modulos/7-t_resize/ix_terminal"
    [[ -d "$ix_mod" ]] && export PYTHONPATH="${ix_mod}:${PYTHONPATH:-}"
    local t_mod="$IX_WP_DIR/1-modulos/7-t_resize"
    [[ -d "$t_mod" ]] && export PYTHONPATH="${t_mod}:${PYTHONPATH:-}"
  fi
  echo "🖥️  Lançando TUI..."
  "$py3" << 'PYEOF'
from __future__ import annotations
import sys
try:
    from ix_terminal_base import IxTerminalApp
    from ix_terminal_helpers import run_cmd
except ImportError:
    print("ix_terminal nao disponivel. Usando menu bash.")
    sys.exit(1)
from textual.binding import Binding
from textual.widgets import RichLog
PROJECT_NAME = "ix.BLZ-S(DS+UTM)"
MENU_SECTIONS = [("Projeto", [("s", "Start", "Iniciar projeto")])]
ACTION_MAP = {"start": "\u25b6 Start"}
class ix_BLZ_S_DS_UTM_App(IxTerminalApp):
    PROJECT_NAME = PROJECT_NAME
    MENU_SECTIONS = MENU_SECTIONS
    ACTION_MAP = ACTION_MAP
    BINDINGS = [Binding("s", "go('start')", "Start", show=True), Binding("q", "quit", "Sair")]
    async def action_handler_start(self, log: RichLog) -> None:
        await run_cmd(log, "echo Hello")
if __name__ == "__main__":
    ix_BLZ_S_DS_UTM_App().run()
PYEOF
  return $?
}
# Tentar TUI primeiro; se falhar, continuar com menu bash abaixo
_try_tui 2>/dev/null || true

# ── Menu interativo (fallback) ────────────────────────────
echo ""
echo "  🚀 ix.BLZ-S(DS+UTM) — ix.WP Launcher"
echo ""
PS3="Escolha: "
select opt in "Abrir VS Code" "Rodar testes" "Sair"; do
  case "$opt" in
    "Abrir VS Code")
      code "$ROOT/ix.BLZ-S(DS+UTM).code-workspace"
      break
      ;;
    "Rodar testes")
      npm test 2>/dev/null || echo "Sem testes configurados"
      ;;
    "Saír") break ;;
    *) echo "Opção inválida" ;;
  esac
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
