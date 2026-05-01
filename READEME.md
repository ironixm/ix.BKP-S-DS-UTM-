<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │  `README.md` – V1.0.0                          │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ READEME.md                                     │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

---

## 📄 `README.md`

```md
# ix.DealScore · UTM Sync

Agente de sincronização incremental para Deals do Pipedrive,
com UI de controle, logs, progresso e cálculo de DealScore.

Projetado para:
- Backfill grande
- Execução segura
- Controle manual
- Zero loop infinito

---

## 🚀 O QUE ESTE PROJETO FAZ

- Sincroniza Deals de um **filtro do Pipedrive**
- Deriva e grava UTMs (opcional)
- Calcula e grava DealScore
- Executa em **lotes controlados**
- Permite **pausar, retomar e observar**

Tudo via uma **UI simples em `/sync-ui`**.

---

## 🧠 PRINCÍPIO DE FUNCIONAMENTO

O Pipedrive **não fornece totals confiáveis**.

Portanto:

> **A sincronização termina quando a API retorna zero deals.**

Nada mais.

---

## 🖥️ INTERFACE

Acesse:

/sync-ui

Campos principais:
- **Filter ID** → ID do filtro no Pipedrive
- **Start** → offset inicial (normalmente 0)
- **Limit** → tamanho do lote
- **Modo**
  - `test` → não grava
  - `write` → grava
- **Intervalo** → tempo entre lotes (segundos)

---

## ▶️ COMO USAR (FLUXO NORMAL)

1. Acesse `/sync-ui`
2. Preencha:
   - Filter ID
   - Start = 0
   - Limit = 50 (ou menor para testes)
3. Clique em **Iniciar**
4. Observe:
   - Logs
   - Links dos deals processados
   - Progresso visual
5. Aguarde o encerramento automático

---

## ⏸️ PAUSAR / RETOMAR

- **Pausar** interrompe o timer
- **Retomar** continua do mesmo `start`
- O estado é salvo no navegador

---

## 📦 ESTRUTURA DO PROJETO

```
.
├── main.py                # API Flask
├── pd_api.py              # Integração Pipedrive
├── dealscore/             # Lógica de score
├── templates/
│   └── sync_ui.html       # UI
├── static/
│   └── sync_ui.js         # Loop + controle
└── AGENT.md               # Guia do agente
```

---

## ⚠️ ALERTAS IMPORTANTES

- **Nunca** use `pagination.more_items_in_collection` para parar
- **Nunca** use `total_items` para controle de fluxo
- O único critério de parada é:
  ```js
  results.length === 0

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
