<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – Pushover – V1.0.0                                 │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/_services/pushover/AGENT.md │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# AGENTE – Pushover

## Quando usar
- Decisoes pendentes do usuario
- Pontos criticos (bloqueios, erros, risco de regressao)
- Inicio e termino de processos longos

## Comandos
```bash
python3 _services/pushover/pushover.py send --title "Decisao" --message "Descreva a escolha" --priority 1
python3 _services/pushover/pushover.py disable
python3 _services/pushover/pushover.py enable
```

## Observacoes
- Se o usuario disser "pausar pushover" ou "ativar pushover", execute os comandos acima.
- Nunca envie dados sensiveis no corpo da mensagem.
- Antes de finalizar a conversa, enviar 1 paragrafo com resumo do que foi feito, decisoes pendentes do usuario e proximos passos.

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
