# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Factory – V1.0.1                               │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/project_template/core/factory.py │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.1 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝


from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from config import DevelopmentConfig
from core.filters import register_filters
from core.routes_loader import register_blueprints
from core.teardown import register_teardown
from extensions import db, login_manager, migrate

BASE_DIR = Path(__file__).resolve().parents[1]


def create_app(config_object: str | None = None) -> Flask:
    load_dotenv(BASE_DIR / ".env.dev", override=False)
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    register_blueprints(app)
    register_filters(app)
    register_teardown(app)

    jobs_root = app.config.get("JOBS_ROOT")
    if jobs_root:
        os.makedirs(jobs_root, exist_ok=True)

    @app.context_processor
    def inject_app_config():
        return {"app_config": app.config}

    return app
