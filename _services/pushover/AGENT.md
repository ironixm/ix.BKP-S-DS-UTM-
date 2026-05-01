<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – Pushover – V1.0.0                     │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-12 - 08:02         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _services/pushover/AGENT.md                    │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# AGENTE – Pushover

## Quando usar
- Decisoes pendentes do usuario
- Pontos criticos (bloqueios, erros, risco de regressao)
- Inicio e termino de processos longos

### Comportamento padrão
Crie todas as tarefas solicitadas a um AGENT em /_docs/JOBS.md, crie os "ToDos(Copillot)/Tasks(CODEX)" para acompanhamento visual do andamento, e vá me mantendo informado sempre via /_services/pushover, a cada:
1 - Fechamento de tarefas
2 - Decisões importantes tomadas por você
3 - Decisões que eu preciso tomar
4 - Erros críticos
5 - De 5 em 5 minutos com o estado atual
6 - Ao finalizar o sumário do que foi feito

### Prompt padrão para colar e retomar o envio de mensagens push durante o processo de um AGENT:

```md
---
**Comportamento padrão - ATIVAR PUSHOVER**
Crie todas as tarefas solicitadas a um AGENT em /_docs/JOBS.md, crie os "ToDos(Copillot)/Tasks(CODEX)" para acompanhamento visual do andamento, e vá me mantendo informado sempre via /_services/pushover, a cada:
1 - Fechamento de tarefas
2 - Decisões importantes tomadas por você
3 - Decisões que eu preciso tomar
4 - Erros críticos
5 - De 5 em 5 minutos com o estado atual
6 - Ao finalizar o sumário do que foi feito
```

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

## Acesso a chaves
- Neste próprio pacote você encontrará o acesso as chaves em /_services/pushover/.env.pushover

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
