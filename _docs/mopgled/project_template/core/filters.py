# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Filters – V1.0.1                               │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/project_template/core/filters.py │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.1 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝


from __future__ import annotations

from datetime import datetime

from flask import Flask


def _format_dt(value: datetime | None) -> str:
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y %H:%M")


def register_filters(app: Flask) -> None:
    app.jinja_env.filters["format_dt"] = _format_dt
