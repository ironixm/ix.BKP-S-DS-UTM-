<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Changelog – V1.0.0                             │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-16 - 14:26         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ CHANGELOG.md                                   │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# Changelog

Todas as mudancas relevantes deste projeto serao registradas aqui.

## [Unreleased]

### Added
- Estrutura ix.WP aplicada: README, CHANGELOG e JOBS na raiz.
- Workflows GitHub de validacao de commit e orquestracao de merge.
- Estrutura inicial do modulo Sonhos (SONHOS.md e _docs/sonhos/).
- Configuracao ix_tagger via .vscode/settings.json.
- Script de build/sync do Mopgled em scripts/build_mopgled.sh.
- Assets de branding base (logo, favicon e icon).
- JOBS.db com 27 tarefas (4 fases de execução + backlog + concluídas)
- Prompt de continuidade: `_docs/prompts/260416-1555-EnrichV2-Execucao4Fases(Prompt).md`

### Changed
- templates/base.html com metadata e favicon de projeto.
- `scripts/batch_enrich.py`: consolidou 4 update_deal em 1 PUT (economia ~30 tokens/deal)
- `scripts/batch_enrich.py`: budget tracking diário (60k tokens Growth) + sistema de resume
- `pd_api.py`: rate limit global 0.25s throttle + 429 retry + fail-fast
- `notes_builder.py`: marcador de notas auto `<div data-ix="ix.auto.dealscore">` (fix duplicatas)
- `JOBS.md` e `_docs/_JOBS/JOBS.md`: 4 fases de trabalho priorizadas (DealScore fix, API v2, produtos, batch)

### Fixed
- Bug de notas duplicadas: Pipedrive remove HTML comments, marcador migrado para `data-ix` attribute
- Deal 22256: 6 notas duplicadas removidas

### Notes
- Processo de iHFM aplicado em modo automatico para ampliar cobertura de headers.
- Plano Pipedrive identificado como Growth (1 seat) via `x-ratelimit-limit: 40`
- 10+ divergências auditadas entre `deal_score_metodologia.md` e `deal_score_rules.py`
- Enrichment v2 planejado: 7 passos/deal, ~54 tokens/deal, ~1.100 deals/dia

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
