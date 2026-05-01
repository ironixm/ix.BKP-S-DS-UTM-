<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – ix.BZP-DealScore-UTM-Sync – V1.0.0    │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _docs/mopgled/project_template/AGENT.md        │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# AGENTE – ix.BZP-DealScore-UTM-Sync

## Objetivo do projeto
- Defina o objetivo no `_docs/JOBS.md` e mantenha atualizado.

## Leitura inicial
1. `_docs/entrada/mopgled/AGENT.md`
2. `_docs/_cHead.md`
3. `_docs/AGENT.md`

## Estrutura principal
- `core/` – app factory, routes base, login e saúde.
- `models/` – modelos SQLAlchemy.
- `migrations/` – Alembic.
- `modulos/` – módulos reutilizáveis (inclui MopGled Client).
- `static/` – assets estáticos.
- `templates/` – templates do CORE.
- `_services/` – micro-serviços auxiliares (ex.: Pushover).
- `_docs/` – documentação, playbooks e prompts.

## Aprofundar por área
- Backend: leia `core/AGENT.md` e `models/AGENT.md`.
- Migrations: leia `migrations/AGENT.md`.
- UI/Templates: leia `templates/AGENT.md`.
- Estáticos: leia `static/AGENT.md`.

## Fluxo obrigatório
1. Leia `_docs/_cHead.md`.
2. Atualize `_docs/JOBS.md` antes e depois de cada entrega.
3. Registre prompts em `_docs/Prompts/`.
4. Siga `.github/COMMIT_CONVENTION.md`.

## Como rodar
- Ative a venv e rode `_Start(▶︎)_.command`.

## Importante
- `modulos/mopgled-client` é obrigatório e deve ser mantido atualizado.
- Se o layout não estiver carregando, verifique `templates/base.html` e `static/mopgled.css`.

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
