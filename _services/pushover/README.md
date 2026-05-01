<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Pushover (micro-servico) – V1.0.0              │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-12 - 07:48         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _services/pushover/README.md                   │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# Pushover (micro-servico)

Use este micro-servico para notificar:
- pontos criticos
- decisoes pendentes
- inicio/fim de processos

Ele também sugere a criação de todas as tarefas solicitadas a um AGENT em /_docs/JOBS.md, a criação de "ToDos(Copillot)/Tasks(CODEX)" para acompanhamento visual do andamento, e ir me mantendo informado sempre via /_services/pushover, a cada:
1 - Fechamento de tarefas
2 - Decisões importantes tomadas por você
3 - Decisões que eu preciso tomar
4 - Erros críticos
5 - De 5 em 5 minutos com o estado atual
6 - Ao finalizar o sumário do que foi feito

## Comandos rapidos
```bash
python3 _services/pushover/pushover.py send --title "Decisao" --message "Descreva a escolha" --priority 1
python3 _services/pushover/pushover.py disable
python3 _services/pushover/pushover.py enable
```

## Variaveis de ambiente
- `PUSHOVER_USER_KEY`
- `PUSHOVER_API_TOKEN` (ou `PUSHOVER_API_KEY`)
- `PUSHOVER_ENABLED` (opcional: 0/1)

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
