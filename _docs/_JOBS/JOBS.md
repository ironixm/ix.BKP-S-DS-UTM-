# JOBS — 2026-04-16 15:55

> Gerado por sessao Copilot + ix.WP-EXT jobsManager | Fonte: _docs/_JOBS/jobs.db

## 📊 Resumo

| Métrica | Valor |
|---------|-------|
| Total | 27 |
| Em aberto (todo) | 18 |
| Concluídos | 9 |
| P0 abertas | 4 |
| P1 abertas | 9 |

## 🔴 P0 — Críticas

- [ ] [F1] Alinhar deal_score_rules.py com deal_score_metodologia.md — 10+ divergências
- [ ] [F1] Implementar score_activities() — contagem de atividades ausente
- [ ] [F1] Implementar stagnation caps — ≥30d max 100, ≥60d max 60
- [ ] [F1] Corrigir movimento real (estagnação) — usar last_activity_time

## 🟡 P1 — Alta Prioridade

### Fase 1 — DealScore
- [ ] [F1] Corrigir funil virtual — ix.B→BOFU, KTL, F1/F2/F3
- [ ] [F1] Decidir emojis com operador — 🧊👀⚡🔥 vs 🪨🌱🌿🌳🍀

### Fase 2 — API v2
- [ ] [F2] Migrar pd_api.py para endpoints v2 — economia ~50% tokens
- [ ] [F2] Cursor pagination nos batch scripts

### Fase 3 — Auto-Produtos
- [ ] [F3] Alinhar preços dos tiers com deals won recentes
- [ ] [F3] Implementar auto-assign produtos via bulk endpoint

### Fase 4 — Batch Run
- [ ] [F4] Rodar batch_enrich.py — 12 meses, recente→antigo
- [ ] [F4] Limpar notas duplicadas remanescentes

### Infra
- [ ] [Infra] Migrar deploy para Coolify/pi5-work (ls.alx-i.com)

## 🔵 P2/P3 — Backlog

- [ ] [F2] include_fields para reduzir payload
- [ ] [F3] Configurar billing_frequency nos produtos
- [ ] [Sonho] Testes de regressão DealScore
- [ ] [Sonho] Pipeline incremental com checkpoints
- [ ] [Sonho] Dashboard de saúde operacional [P3]

## ✅ Concluídos (sessão 2026-04-15/16)

- [x] Corrigir bug notas duplicadas (marcador data-ix) — 15/04
- [x] Adicionar rate limit global pd_api.py — 15/04
- [x] Limpar duplicatas deal 22256 — 15/04
- [x] Otimizar batch_enrich.py — 4 PUTs→1 — 16/04
- [x] Budget tracking + resume no batch_enrich.py — 16/04
- [x] Pesquisar rate limits Pipedrive token-based — 16/04
- [x] Identificar plano Growth via headers + features — 16/04
- [x] Auditar divergências doc vs código DealScore — 16/04
- [x] Planejar Enrichment v2 completo (7 passos, 4 fases) — 16/04

---
_Atualizado: 2026-04-16 15:55 (America/Sao_Paulo) — Fonte: jobs.db_
