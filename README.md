<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ ix.BLZ-S(DS+UTM) – V1.0.0                      │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-16 - 14:26         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ README.md                                      │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# ix.BLZ-S(DS+UTM)

Projeto de sincronizacao, enrich e analise de dados comerciais com foco em DealScore, UTM e automacoes operacionais.

## Visao Geral / Overview

A aplicacao integra dados de CRM, aplica regras de score e gera atualizacoes operacionais em lote para apoiar o funil comercial.

Objetivos principais:
- Consolidar dados de deals, pessoas e organizacoes.
- Calcular/atualizar DealScore com regras padronizadas.
- Automatizar enrich, notas e normalizacao de datas.
- Expor UI auxiliar para operacao (sync e datas).

## Stack / Tecnologias

- Python 3 (automacao, API wrappers, regras de negocio)
- HTML + CSS + JavaScript (UI auxiliar)
- Flask-style templates (paginas em templates/)
- Integracoes: Pipedrive, Pushover, Linear
- Suporte operacional ix.WP (instrucoes, workflows e utilitarios)

## Estrutura do Projeto

- main.py: entrada da aplicacao web e rotas auxiliares
- dealscore/: regras e calculo de score
- scripts/: rotinas batch e analises
- templates/: telas auxiliares (sync/dates/mopgled)
- static/: assets frontend
- modulos/mopgled/: pacote de integracao visual Mopgled
- _docs/: documentacao tecnica, jobs e materiais de suporte

## Modulos / Features

- DealScore: calculo e atualizacao de score por deal
- Enrich batch: processamento em lote com controle de progresso
- Normalizacao de datas: UI/API para ajustes em massa
- Rich notes: geracao/atualizacao de notas automatizadas
- Integracao Mopgled: includes de tema e autosync de assets
- Operacao ix.WP: conventions, prompts e automacoes de projeto

## Setup / Como Rodar

### 1) Ambiente

- Configure o .env com as credenciais operacionais.
- Configure o .env.wp com variaveis ix.WP e integracoes.

### 2) Dependencias

Com Poetry:

```bash
poetry install
```

Com pip:

```bash
pip install -r requirements.txt
```

### 3) Execucao local

```bash
python3 main.py
```

Acesse as UIs:
- /sync-ui
- /dates-ui

### 4) Rotinas batch

Exemplos:

```bash
python3 scripts/batch_enrich.py
python3 scripts/batch_update_all_scores.py
python3 scripts/clean_duplicate_notes.py
```

## Observacoes

- Timezone padrao operacional: America/Sao_Paulo.
- Diretório temporario: usar sempre ./tmp.
- Commits e PRs seguem padrao ix.WP (.gitmessage e pull_request_template).

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
