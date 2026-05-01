<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ ix.BLZ-S(DS+UTM) — Projeto V2.0                           │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-16                              │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                              │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                                   │║ -->
<!-- # ║      ▜▛       │ _docs/projeto/Projeto-V2.0.md                              │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Evolução de: Projeto-ix.BLZ-S-DS-UTM-V1.0-190326.md        │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# Projeto-ix.BLZ-S(DS+UTM) V2.0

> **Evolução de:** Projeto-ix.BLZ-S-DS-UTM-V1.0-190326.md
> **Data:** 2026-04-16 | **Autor:** Ir.On | **Stack:** Python / GAS / GSheets / Pipedrive

---

## Visão Geral / Overview

Suite de automação e analytics para o funil comercial ix.BZL-S. Integra dados do CRM Pipedrive,
aplica regras de DealScore, realiza enrich em lote e expõe uma UI auxiliar para operação (sync de
deals, normalização de datas). Suporte operacional via ix.WP com notificações Pushover e rastreamento
no Linear.

**O que mudou e por quê (V1 → V2):**
- V1: foco em portfolio/classificação, stack apenas descrita
- V2: projeto em operação real — DealScore ativo, enrich batch rodando, UI auxiliar funcional,
  ix.WP completamente provisionado (iHFM, Branding, Mopgled, Sonhos, etc.)

---

## Objetivos

- Calcular/atualizar DealScore com regras padronizadas e auditáveis
- Automatizar enrich, notas ricas e normalização de datas em lote
- Manter operação contínua com alertas Pushover e controle via Linear
- Servir como referência de projeto-padrão ix.WP para futuros projetos FVR

---

## Público / Agentes Envolvidos

- **Operador:** Ir.On (Iron Mascarenhas) — proprietário e operador principal
- **Agente Copilot:** executor de tarefas, geração e revisão de código
- **Agente Linear:** Alixia-A — gerenciamento de backlog e JOBS
- **CRM:** Pipedrive — fonte de dados de deals, pessoas e organizações

---

## Escopo

**Dentro do escopo:**
- Scripts Python de automação (batch_enrich, batch_update_all_scores, clean_duplicate_notes)
- Sistema de DealScore (regras, cálculo, atualização em lote)
- UI auxiliar (sync_ui, dates_ui)
- Integração Mopgled (assets CSS/JS, include templates)
- Operação ix.WP (iHFM, Branding, Pushover, Linear, Sonhos)

**Fora do escopo:**
- Dashboard de analytics completo (Sonho — roadmap)
- API pública de DealScore
- Automação de marketing (UTM tracking — escopo futuro)

---

## Estratégia

Discovery incremental orientado por evidências do repositório. Cada melhoria passa por ciclo:
hipótese → menor intervenção possível → teste → registro → commit. Priorização por impacto × risco.
ix.WP governa convenções, documentação e automações operacionais.

---

## Arquitetura / Structure

```
ix.BLZ-S(DS+UTM)/
├── main.py                  ← Entrada Flask (rotas + UI auxiliar)
├── dealscore/               ← Regras e cálculo de score
│   ├── deal_score.py
│   └── deal_score_rules.py
├── scripts/                 ← Rotinas batch e análises
├── templates/               ← UI auxiliar (sync_ui, dates_ui, mopgled)
├── static/                  ← Assets frontend + brand
├── modulos/mopgled/         ← Pacote de integração visual Mopgled
├── _docs/                   ← Documentação técnica, JOBS, contextos salvos
├── _marca/                  ← Identidade visual do projeto
└── _services/pushover/      ← Módulo de notificações
```

---

## Stack / Tecnologias

- **Python 3** — automação, API wrappers, regras de negócio (pyproject.toml / Poetry)
- **Flask** — servidor web auxiliar, rotas de UI
- **HTML + CSS + JavaScript** — UI auxiliar (sync_ui, dates_ui)
- **Pipedrive API** — fonte de dados CRM (deals, persons, organizations)
- **Pushover API** — canal único de notificações (12 níveis, branding sonoro)
- **Linear API** — rastreamento de backlog e JOBS (Alixia-A)
- **Google Apps Script** — PipedrivePull.gs para sync via GSheets
- **Mopgled** — sistema de assets CSS/JS com autosync CDN

---

## Módulos / Features

| Módulo | Status | Descrição |
|--------|--------|-----------|
| DealScore | ✅ Ativo | Cálculo e atualização de score por deal (regras em deal_score_rules.py) |
| Enrich batch | ✅ Ativo | Processamento em lote com controle de progresso |
| Normalização de datas | ✅ Ativo | UI/API para ajustes em massa de datas de deals |
| Rich notes | ✅ Ativo | Geração/atualização de notas automatizadas |
| Mopgled | ✅ Ativo | Includes de tema e autosync de assets CSS/JS |
| LTV analysis | ✅ Ativo | Análise de lifetime value por cliente |
| ix.WP operations | ✅ Ativo | Conventions, prompts, automações e governance |

---

## Setup / Como Rodar

### 1) Pré-requisitos

- Python 3.9+
- Poetry ou pip
- Credenciais Pipedrive, Pushover, Linear em `.env` e `.env.wp`

### 2) Instalar dependências

```bash
poetry install
# ou
pip install -r requirements.txt
```

### 3) Configurar variáveis

```bash
cp .env.example .env   # configurar PIPEDRIVE_API_TOKEN, etc.
# .env.wp já versionado com estrutura (credenciais locais)
```

### 4) Executar servidor local

```bash
python3 main.py
# Acesse: http://localhost:5000/sync-ui
#         http://localhost:5000/dates-ui
```

### 5) Rotinas batch

```bash
python3 scripts/batch_enrich.py
python3 scripts/batch_update_all_scores.py
python3 scripts/clean_duplicate_notes.py
```

### 6) Build Mopgled (assets)

```bash
npm run build
# ou diretamente:
bash scripts/build_mopgled.sh
```

---

## Indicadores / Critérios de Aceite

- DealScore atualizado em < 2s por deal
- Enrich batch com 0 erros silenciosos (todos logados)
- UI: normalização de datas funcional end-to-end
- ix.WP: score de conformidade ≥ 90%

---

## Riscos e Dependências

- **Pipedrive API rate limit:** mitigado com delays em batch scripts
- **ix.WP non-compliance:** monitorado via health check periódico
- **Credentials exposure:** `.env` e `.env.wp` gitignored; nunca versionados

---

## Roadmap

- [ ] Dashboard de saúde operacional (Sonho #3)
- [ ] Pipeline incremental com checkpoints (Sonho #2)
- [ ] Testes de regressão DealScore (Sonho #1)
- [ ] UTM tracking ativo (escopo futuro)

---

## Governança

- **Dono técnico:** Iron Mascarenhas (Ir.On / ironix.com.br)
- **Revisão:** semanal para ciclos ativos
- **Commits:** padrão `feat:|fix:|refactor:|docs:|chore:` (ver .gitmessage)
- **Backlog:** JOBS.md + Linear (Alixia-A)
- **ix.WP:** V3.2.1 — todos os módulos ativos

---

## Evolução do Projeto

**V1.0 (2026-03-19):** Foco em portfolio. Stack descrita, projeto catalogado.
**V2.0 (2026-04-16):** Projeto em operação real. ix.WP completamente provisionado.
Divergências detectadas: stack evoluiu (Mopgled, ix.WP, Pushover, Linear ativos),
features não previstas no V1 dominam o projeto. Novo documento reflete realidade atual.
