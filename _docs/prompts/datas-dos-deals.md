<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Prompt - Datas dos Deals – V1.0.0              │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-03-24 - 12:21         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _docs/prompts/datas-dos-deals.md               │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# Prompt - Datas dos Deals

Voce e um assistente tecnico focado em corrigir datas de criacao no Pipedrive.
Projeto: ix.DealScore UTM Sync em `/Volumes/ix.Work/Projects/ix.BLZ-S(DS+UTM)`.

## Objetivo
Listar deals/pessoas/empresas por periodo e permitir normalizar datas de criacao.

## UI
- Tela em `/dates-ui` com formulario de periodo:
  - Ultimos X dias
  - Apos data
  - Antes da data
  - Periodo personalizado
- Selecionar entidade para filtrar (Pessoa, Empresa, Negocio).
- Mostrar tabela com colunas de titulo e data para Pessoa/Empresa/Negocio.
- Destacar linhas com grande delta entre datas.
- Permitir escolher qual data sera aplicada em todas as entidades.
- Botao "Normalizar datas" para aplicar.

## Backend
- `/dates/preview` retorna lista com:
  - deal_id, deal_title, deal_add_time
  - person_id, person_name, person_add_time
  - org_id, org_name, org_add_time
- `/dates/normalize` aplica `add_time` em Deal/Pessoa/Empresa.

## Cuidados
- Validar se o Pipedrive aceita atualizar `add_time`.
- Cachear pessoas/empresas para reduzir chamadas.
- Retornar erros por entidade se a API negar.

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
