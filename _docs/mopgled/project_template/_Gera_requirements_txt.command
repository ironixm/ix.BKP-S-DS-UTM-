#!/usr/bin/env bash
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │  Gera Requirements Txt – V1.0.1                            │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║
# ║ ██ ▀ ████████ │ commit:f563b5b                                             │║
# ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ _docs/mopgled/project_template/_Gera_requirements_txt.c... │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * V1.0.1 - [sem detalhes]                                  │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# _Gera_requirements_txt.command
# Versao: V1.0.0 – Base de requirements automatizada
# Assinado por: ix.BZP-DealScore-UTM-Sync

set -euo pipefail
cd "$(dirname "$0")"

PYBIN="${PYBIN:-python3}"
PIP="$PYBIN -m pip"

# 0) Garante pipreqs e pip-compile disponíveis
if ! $PYBIN -m pipreqs --help >/dev/null 2>&1; then
  echo "🧰 Instalando pipreqs..."
  $PIP install pipreqs
fi
if ! $PYBIN -m piptools --help >/dev/null 2>&1 && ! command -v pip-compile >/dev/null 2>&1; then
  echo "🧰 Instalando pip-tools..."
  $PIP install pip-tools
fi

PIPREQS_CMD="$PYBIN -m pipreqs"
if command -v pipreqs >/dev/null 2>&1; then PIPREQS_CMD="pipreqs"; fi
PIP_COMPILE_CMD="$PYBIN -m piptools compile"
if command -v pip-compile >/dev/null 2>&1; then PIP_COMPILE_CMD="pip-compile"; fi

echo
echo "🔍 1) Detectando imports com pipreqs..."
"$PIPREQS_CMD" . \
  --force \
  --ignore=".venv,__pycache__,.history,migrations,_docs,static,tests" \
  --savepath=requirements.auto.in

echo
echo "✏️ 2) Inserindo bloco base..."
cat >> requirements.auto.in <<'EOF'

# --- Base obrigatoria ---
Flask==2.3.3
Flask-Login==0.6.3
Flask-Migrate==4.1.0
flask-sqlalchemy==3.1.1
python-dotenv==1.1.1
gunicorn==23.0.0
psycopg2-binary==2.9.10
EOF

echo
echo "⚙️ 3) Compilando requirements.txt..."
"$PIP_COMPILE_CMD" requirements.auto.in --output-file=requirements.txt

echo
echo "🎉 requirements.txt pronto em: $(pwd)/requirements.txt"

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
