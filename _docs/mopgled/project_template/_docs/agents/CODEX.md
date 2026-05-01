<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – CODEX – V1.0.0                                    │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/_docs/agents/CODEX.md       │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# AGENTE – CODEX

## Checklist obrigatório
- Leia `_docs/_cHead.md`.
- Leia `_docs/playbooks/#9.1 Playbook Projecter-V-CODEX.md`.
- Atualize `_docs/JOBS.md` no início e no fim.

## Regras de commit/deploy
- Seguir `.github/COMMIT_CONVENTION.md`.
- Descrever mudanças no corpo do commit.

## Estado e memória
- Salvar prompts relevantes em `_docs/Prompts/`.
- Assinar tarefas concluídas em `_docs/JOBS.md`.

## Pushover
- Notifique pontos críticos, decisões e início/fim de processos:
  `python3 _services/pushover/pushover.py send --title "Decisao" --message "Descreva a escolha" --priority 1`
- Pausar/ativar:
  `python3 _services/pushover/pushover.py disable` / `python3 _services/pushover/pushover.py enable`

## Finalizacao de conversa
- Antes de finalizar, envie 1 paragrafo com: resumo do que foi feito, decisoes pendentes do usuario e proximos passos.

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
