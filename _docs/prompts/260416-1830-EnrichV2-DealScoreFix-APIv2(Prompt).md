<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Prompt de Continuidade — Enrich v2 + DealScore Fix + AP... │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-04-16 - 13:39                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/prompts/260416-1830-EnrichV2-DealScoreFix-APIv2(P... │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# Prompt de Continuidade — Enrich v2 + DealScore Fix + API v2
> Sessão: 2026-04-16 | Projeto: ix.BLZ-S(DS+UTM) | Agent: Copilot CLI (ZeroPC)

---

## TL;DR — O que ficou pendente

Sessão anterior (VS Code Copilot) fez planejamento completo do Batch Enrichment v2. Auditou 10+ divergências entre `deal_score_metodologia.md` e o código, otimizou batch_enrich.py (4 PUTs → 1), adicionou budget tracking e resume. **Nenhum código de correção do DealScore foi aplicado ainda**. O batch NÃO foi rodado.

**Próximo passo imediato**: Fase 1 — corrigir DealScore rules, depois migrar para API v2, depois rodar o batch.

---

## Contexto do Projeto

Projeto Python (Flask) que sincroniza deals do Pipedrive com enriquecimento automático:
- DealScore (scoring de 15+ critérios → priorização operacional)
- Emoji prefix no título (🪨🌱🌿🌳🍀 ou 🧊👀⚡🔥 — pendente decisão)
- Rich Notes com seção manual preservada + auto gerada
- LTV/Tenure/ConversionValue auto-calculation
- Auto-product assignment (Setup + Mensalidade)
- UTM sync Deal → Person

### Estrutura de arquivos chave
```
dealscore/deal_score_rules.py    ← regras e pesos do DealScore
dealscore/deal_score.py          ← engine de cálculo
pd_api.py                        ← wrapper Pipedrive API (v1, com rate limit)
main.py                          ← Flask app + webhook handler + emoji tiers
notes_builder.py                 ← Rich Notes HTML builder
scripts/batch_enrich.py          ← batch processor (otimizado, com resume)
scripts/clean_duplicate_notes.py ← limpeza de notas duplicadas
product_match.py                 ← tiers de produto por DealScore
ltv.py                           ← cálculo LTV
mappings.py                      ← field keys Pipedrive
parsers.py                       ← parse_meta_campaign (UTM → campos isolados)
_docs/deal_score_metodologia.md  ← fonte de verdade do DealScore
_docs/JOBS.md                    ← tracking de tarefas
```

### Pipedrive
- **Plano**: Growth (1 seat) — confirmado via `x-ratelimit-limit: 40` + multi-pipeline
- **Budget diário**: 60.000 tokens (30k base × 2 Growth × 1 seat)
- **API key**: em `.env` como `PIPEDRIVE_API_KEY`
- **Company domain**: buzzlead
- **Rate limit atual em pd_api.py**: 0.25s throttle + 429 retry + fail-fast se >300s

---

## Fase 1 — Corrigir DealScore (PRIORIDADE MÁXIMA)

### Divergências doc vs código (fonte de verdade: `_docs/deal_score_metodologia.md`)

**Em `dealscore/deal_score_rules.py`:**

| Item | Doc (correto) | Código (errado) | Ação |
|------|---------------|-----------------|------|
| STAGE Levantada Mão | +5 | +10 | Corrigir → +5 |
| STAGE Agendado | +35 | +30 | Corrigir → +35 |
| STAGE Negociação | +90 | +120 | Corrigir → +90 |
| STAGE Quarentena | +5 | 0 (reset) | Corrigir → +5 (não zera mais) |
| FUNIL MOFU | +10 | +15 | Corrigir → +10 |
| FUNIL BOFU | +20 | +30 | Corrigir → +20 |
| SITE válido/inválido | +10/-10 | +15/-15 | Corrigir → +10/-10 |
| EMAIL válido | +5 | +10 | Corrigir → +5 |
| PHONE válido | +5 | +10 | Corrigir → +5 |
| QUESTIONÁRIO Não | -10 | 0 | Corrigir → -10 |
| EMAIL empresarial | 0 (neutro) | +10 | Corrigir → 0 |
| PROBABILIDADE | 0 (não contribui) | max 50 | Corrigir → 0 |
| ESTAGNAÇÃO | 7 buckets (0 a -120) | 5 buckets (0 a -40) | Expandir para 7 buckets |

**Em `dealscore/deal_score.py`:**

| Item | Ação |
|------|------|
| score_funil() | ix.F→BOFU está errado, deve ser ix.B→BOFU. Adicionar KTL pattern e F1/F2/F3 fallback |
| score_stagnation() | Usar max(last_activity_time, stage_change_time) fallback update_time |
| score_activities() | **Implementar** — NÃO existe. Buckets: 0=-10, 1=0, 2-3=+5, 4-5=+10, 6-10=+8, 11+=+4 |
| Stagnation caps | **Implementar** — dias≥30 → score max 100, dias≥60 → score max 60 |
| Quarentena | Remover de RESET_STAGES, dar +5 em STAGE_SCORES |

### NOTA sobre emojis — DECISÃO PENDENTE DO USUÁRIO
- Doc oficial: 🧊(≤0) 👀(1-100) ⚡(101-200) 🔥(201+)
- Código atual: 🪨(<0) 🌱(0-49) 🌿(50-149) 🌳(150-249) 🍀(250+)
- Perguntar ao usuário qual set manter antes de alterar

---

## Fase 2 — Migrar para API v2

Referência: https://pipedrive.readme.io/docs/pipedrive-api-v2

Em `pd_api.py`:
- Criar `BASE_URL_V2 = "https://api.pipedrive.com/api/v2"`
- Novos wrappers `get_deal_v2()`, `update_deal_v2()`, `get_person_v2()` etc
- Manter v1 para endpoints sem suporte v2 (notes, products/bulk)
- Usar cursor pagination em batch scripts
- `include_fields=activities_count,products_count` no GET deal
- Economia: ~50% tokens (PATCH deal 5 vs 10, GET deal 1 vs 2)

---

## Fase 3 — Auto-Produtos com Billing

Em `product_match.py` e `scripts/batch_enrich.py`:
- Alinhar SETUP_TIERS e MENSALIDADE_TIERS com preços reais dos deals won recentes
- Se `products_count > 0` → NÃO mexer (vendedor ajustou)
- Se `products_count == 0` → POST /api/v2/deals/{id}/products/bulk com Setup (one-time) + Mensalidade (monthly, 12 ciclos)
- Dados conhecidos dos prints: Setup Premium R$5900, Mensalidade entre R$749 e R$849

---

## Fase 4 — Rodar Batch Enrichment

Em `scripts/batch_enrich.py` (já otimizado):
- Consolida 4 update_deal em 1 PUT (economia ~30 tokens/deal)
- Budget tracking com estimativa de tokens
- Resume system: salva progresso em `.batch_progress.txt`
- Sort: mais recente → mais antigo
- Status: open + won, últimos 12 meses
- Estimativa: ~27 tokens/deal (v2, sem produtos) ou ~52 (com produtos)
- Budget 60k/dia → ~1.150-2.200 deals/dia

---

## Commits não publicados (origin/main está em a8ce695)

```
c16905a fix: corrige anotacoes duplicadas e adiciona rate limit global
214f657 feat: batch_enrich supports 'all' mode
64dec54 feat: add LTV/Tenure/ConversionValue auto-calculation
6326410 feat: add Mensalidade tiers to auto-product
50e4361 feat: implement 4 features (Emoji, Rich Notes, Auto-product, Deal Value)
```

Arquivos unstaged:
- `scripts/batch_enrich.py` (otimização de consolidação + budget tracking)
- 2 prompts corrigidos
- 1 resumo atualizado

Untracked (podem ser úteis):
- `scripts/analyze_ltv.py`
- `scripts/ltv_analysis.json`
- `scripts/won_products_analysis.json`

---

## Comandos úteis

```bash
# Rodar batch (modo all, para em budget limit)
cd /Users/IronMascarenhas_1/Projects/ix.BLZ-S(DS+UTM)
python scripts/batch_enrich.py all

# Limpar duplicatas de notas
python scripts/clean_duplicate_notes.py all

# Testar DealScore de 1 deal
python -c "from pd_api import get_deal, get_person; from dealscore.deal_score import compute_deal_score, FIELD_IDS; d=get_deal(DEAL_ID); p=get_person(PERSON_ID); print(compute_deal_score(d, p, FIELD_IDS))"

# Ver rate limit restante
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import requests; r=requests.get(f'https://api.pipedrive.com/v1/deals?limit=1&api_token={os.environ[\"PIPEDRIVE_API_KEY\"]}'); print({h:r.headers.get(h) for h in ['x-ratelimit-limit','x-ratelimit-remaining','x-daily-requests-left']})"
```

---

## Checklist de execução

1. [ ] Corrigir `deal_score_rules.py` (tabela de divergências acima)
2. [ ] Corrigir `deal_score.py` (funil, estagnação, quarentena, activities, caps)
3. [ ] Testar com 5 deals conhecidos — comparar antes/depois
4. [ ] Migrar pd_api.py para v2 (dual v1/v2)
5. [ ] Alinhar preços de produtos (product_match.py)
6. [ ] Implementar auto-assign produtos no batch
7. [ ] Rodar batch enrich (all, 12 meses, recente→antigo)
8. [ ] Monitorar tokens e verificar resume
9. [ ] Atualizar JOBS.md ao completar cada fase
10. [ ] Commit + push após cada fase

---

## Restrições

- NUNCA sobrescrever campos preenchidos manualmente pelo vendedor (LTV, Tenure, produtos)
- NUNCA rodar múltiplas instâncias do batch simultaneamente (causa 429)
- Respeitar rate limit: 0.5s entre deals, fail-fast se daily limit atingido
- Preservar seção manual das Rich Notes
- Manter compatibilidade com webhook handler em main.py

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
