# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Routes Loader – V1.0.1                                     │║
# ║ ██▘       ▝██ │                                                            │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                                   │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║
# ║ ██ ▀ ████████ │ commit:f563b5b                                             │║
# ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║
# ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║
# ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║
# ║      ▜▛       │ Caminho:                                                   │║
# ║               │ _docs/mopgled/project_template/core/routes_loader.py       │║
# ║               ├────────────────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                                  │║
# ║               │ * V1.0.1 - [sem detalhes]                                  │║
# ║               │                                                            │║
# ║               └────────────────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════════════════╝


from flask import Flask

from core.auth import bp as auth_bp
from core.health import bp as health_bp
from core.routes_base import bp as core_bp


def register_blueprints(app: Flask) -> None:
    for bp in (core_bp, auth_bp, health_bp):
        app.register_blueprint(bp)
