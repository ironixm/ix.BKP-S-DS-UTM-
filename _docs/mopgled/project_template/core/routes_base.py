# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Routes Base – V1.0.1                                       │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║
# ║ ██ ▀ ████████ │ commit:f563b5b                                             │║
# ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ _docs/mopgled/project_template/core/routes_base.py         │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * V1.0.1 - [sem detalhes]                                  │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝


from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint("core", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("base.html", page_title="Controle")
