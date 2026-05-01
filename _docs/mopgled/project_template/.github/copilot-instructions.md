<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ MadMode — Copilot Instructions (concise) – V1.0.0          │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/.github/copilot-instruct... │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

<!-- Copilot / AI agent instructions for contributors to MadMode (ix.renomeie branch) -->
# MadMode — Copilot Instructions (concise)

Purpose: give AI coding agents the minimal, high-value knowledge to be productive in this codebase.

**Language policy (OBRIGATÓRIO)**: 
- **TODAS as respostas, comunicações, commits, PRs e interações com usuários devem ser SEMPRE em PT-BR (Português Brasileiro)**.
- Arquivos `AGENT.md` / `.github/copilot-instructions.md` devem ser produzidos em português.
- Comentários em código podem ser em PT-BR ou inglês técnico, conforme o padrão já existente no arquivo.
- Sempre confirme com o revisor humano caso haja dúvida sobre terminologia técnica específica.

**Padrão de commits**: Todos os commits e PRs devem seguir o formato `Vx.y.z - ModuloX|ModuloY - Titulo - TIPO - YYMMDDHHMM` (veja `.github/COMMIT_CONVENTION.md` e `.github/pull_request_template.md` para detalhes e exemplos).

- **Big picture**: this is a Flask application with a small core and many plug-in modules under `modulos/`.
  - `core/` boots the app (`core/factory.py`), registers filters, integrations and loads dynamic modules from `modulos/*/manifest.json`.
  - Each module is plug-and-play: add `modulos/<slug>/manifest.json` + blueprint + optional `models` to register it automatically.
  - The app uses SQLAlchemy + Flask-Migrate (Alembic). `APP_LITE_MODE` is used to avoid heavy initialization when running `flask db` commands.

- **Where to look first (quick map)**
  - `core/factory.py` — app factory and the single best source to understand boot order, APP_LITE_MODE, and background threads.
  - `core/module_loader.py` / `core/routes_loader.py` — how manifests are parsed and blueprints registered.
  - `modulos/*/manifest.json` — per-module metadata (name, slug, blueprint, models, menu, admin_only).
  - `_start.command` — dev start script (hot-reload, `--reload-engine` detection, health-check, logs to `logs/flask_dev.log`).
  - `logs/flask_dev.log` and `logs/` — first place to inspect runtime boot messages and the `🩺 Blueprints carregados...` marker used by the starter.

- **Dev workflows & commands (examples)**
  - Use the repo venv: `source .venv/bin/activate` (script assumes `.venv` exists).
  - Fast dev start (preferred): `./_start.command dev` — it handles reload-engine detection, health-checks, and prints logs to `logs/flask_dev.log`.
  - Alternative: `FLASK_APP=wsgi:application .venv/bin/flask run --host=0.0.0.0 --port=5001` (only pass `--reload-engine poll` when the local `flask` supports it).
  - Production test: `./_start.command prod` or run `gunicorn wsgi:application` (controller supports graceful reload via SIGHUP).
  - DB migrations: use `flask db migrate` / `flask db upgrade` — `core/factory.py` enables UltraLite mode when running these commands.

- **Project-specific conventions that matter to agents**
  - Manifest-first modules: always list module `models` in `manifest.json` so `core` imports them before registering blueprints (avoids SQLAlchemy relationship errors).
  - `APP_LITE_MODE` is set automatically during `flask db` commands; do not initialize heavy integrations (SocketIO, OCR, external OAuth) when this is active.
  - Blueprints sometimes use `admin_only` in their manifest — templates filter menus by that flag in `core/factory.py` (see `inject_madmode_menu`).
  - Background work: `models.sigma_sync.auto_sync_cycle()` and `init_integracoes()` are normally spawned as daemon threads from the factory — avoid blocking operations in the main thread before blueprints are registered.

- **Integration points to inspect before touching code**
  - ΣPersistentDB / `api/sync_sigma.py` and `models/sigma_sync.py` — long-running sync cycle runs on boot.
  - `modulos/configuracoes/integracoes/*` — OAuth clients registration and third-party hooks.
  - `utils/ocr_engine_loader.py` — lazy OCR engine initialization; heavy to import at boot.
  - `logtail` integration in `core/factory.py` (optional import) — avoid removing try/except around it.

- **Common pitfalls and how to avoid them**
  - Do not add heavy blocking work before `register_blueprints` completes; `_start.command` watches for a log marker `🩺 Blueprints carregados`.
  - If you modify module loading, import order matters: use `manifest.json` `models` listing to ensure tables are created/imported first.
  - Watch out for the dev reloader + `watchdog` on macOS (fsevents) — the starter already detects `--reload-engine` capability; only pass it when supported.

- **Example file references (quick shortcuts)**
  - Boot and guards: `core/factory.py`
  - Manifest loader: `core/module_loader.py`
  - Routes & registration: `core/routes_loader.py`
  - Dev start: `_start.command` and `logs/flask_dev.log`
  - Where to add new module: `modulos/<slug>/manifest.json`, `modulos/<slug>/routes.py`, `modulos/<slug>/models.py`

If anything here is unclear or you want more detail in a specific area (database lifecycle, module manifest schema, or the dev start script), say which area and I will expand the doc or merge content from module `AGENT.md` files.

<!--
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
-->
