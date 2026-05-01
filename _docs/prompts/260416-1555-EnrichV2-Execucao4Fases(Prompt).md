# Prompt de Continuidade — Enrich v2: Execução das 4 Fases
> Sessão: 2026-04-16 15:55 | Projeto: ix.BLZ-S(DS+UTM) | Agent: Copilot CLI (ZeroPC)
> Branch: main | Último commit: chore: atualiza JOBS.db + JOBS.md + prompt continuidade

---

## TL;DR

Sessão anterior fez **planejamento completo** do Batch Enrichment v2 e identificou **10+ divergências** entre o doc de metodologia e o código do DealScore. Scripts foram otimizados (4 PUTs→1, budget tracking, resume). ix.WP-EXT foi provisionado (iHFM, branding, AGENTS.md, workflows).

**Nenhuma correção de DealScore foi aplicada ainda. O batch NÃO foi rodado.**

Executar na ordem: Fase 1 → Fase 2 → Fase 3 → Fase 4.

---

## Estado do Repositório

- **Branch**: main
- **Origin**: https://github.com/ironixm/ix.BLZ-S-DS-UTM-.git
- **Pipedrive**: Growth (1 seat), budget 60.000 tokens/dia
- **API Key**: em `.env` como `PIPEDRIVE_API_KEY`
- **Company domain**: buzzlead
- **JOBS.db**: `_docs/_JOBS/jobs.db` — 27 jobs (18 todo, 9 done)

---

## Fase 1 — Corrigir DealScore (4 P0 + 2 P1) ← COMEÇAR AQUI

### Arquivos a editar:
- `dealscore/deal_score_rules.py` — pesos e constantes
- `dealscore/deal_score.py` — engine de cálculo
- `main.py` — EMOJI_TIERS (linha ~66)
- `notes_builder.py` — emoji na build_auto_section

### 1.1 — Corrigir deal_score_rules.py

```python
# STAGE_SCORES — trocar:
STAGE_LEVANTADA_MAO: 10  →  5
STAGE_AGENDADO: 30        →  35
STAGE_NEGOCIACAO: 120     →  90

# Remover STAGE_QUARENTENA de RESET_STAGES, adicionar em STAGE_SCORES:
STAGE_SCORES[STAGE_QUARENTENA] = 5

# FUNIL_SCORES — trocar:
"MOFU": 15  →  10
"BOFU": 30  →  20

# DATA QUALITY — trocar:
SITE_VALIDO_SCORES = {"Sim": 10, "Não": -10}      # era 15/-15
EMAIL_VALIDO_SCORES = {"Sim": 5, "Não": -10}       # era 10/-10
EMAIL_EMPRESARIAL_SCORES = {"Sim": 0, "Não": 0}    # era 10/0
PHONE_VALIDO_SCORES = {"Sim": 5, "Não": -5}        # era 10/-5
QUESTIONARIO_SCORES = {"Sim": 20, "Não": -10}      # era 20/0

# PROBABILIDADE:
PROBABILITY_MAX_POINTS = 0  # era 50

# ESTAGNAÇÃO — expandir para 7 buckets:
STAGNATION_BUCKETS_DAYS = [
    (1, 0),
    (3, -5),
    (7, -15),    # era -10
    (14, -30),   # era -20
    (30, -60),   # novo
    (60, -90),   # novo
    (9999, -120),# era -40
]
```

### 1.2 — Corrigir deal_score.py

```python
# score_funil(): fix ix.F→ix.B
if raw.startswith("ix.B"):    # estava "ix.F"
    return FUNIL_SCORES["BOFU"]

# Adicionar detecção KTL:
if "KTL" in raw or "(K)" in raw or "(L)" in raw or "(T)" in raw:
    return FUNIL_SCORES["TOFU"]

# Adicionar fallback F1/F2/F3:
if "-F1" in raw: return FUNIL_SCORES["TOFU"]
if "-F2" in raw: return FUNIL_SCORES["MOFU"]
if "-F3" in raw: return FUNIL_SCORES["BOFU"]

# score_stagnation(): usar movimento real
def score_stagnation(deal, now):
    activity_dt = _parse_pd_dt(deal.get("last_activity_time"))
    stage_dt = _parse_pd_dt(deal.get("stage_change_time"))
    upd_dt = _parse_pd_dt(deal.get("update_time"))
    ref_dt = max(filter(None, [activity_dt, stage_dt]), default=upd_dt)
    ...

# Implementar score_activities():
def score_activities(deal):
    count = int(deal.get("activities_count") or 0)
    if count == 0: return -10
    if count == 1: return 0
    if count <= 3: return 5
    if count <= 5: return 10
    if count <= 10: return 8
    return 4

# Em compute_deal_score(), adicionar:
parts["activities"] = score_activities(deal)

# Stagnation caps (após calcular total):
stag_days = _days_between(ref_dt, now)
if stag_days and stag_days >= 60:
    total = min(total, 60)
elif stag_days and stag_days >= 30:
    total = min(total, 100)

# Quarentena: remover o early return de RESET_STAGES
# O stage_score de Quarentena agora é +5 (via STAGE_SCORES)
```

### 1.3 — Decidir emojis (PERGUNTAR ao operador)
- Doc: 🧊(≤0) 👀(1-100) ⚡(101-200) 🔥(201+) — 4 faixas
- Código: 🪨(<0) 🌱(0-49) 🌿(50-149) 🌳(150-249) 🍀(250+) — 5 faixas

### 1.4 — Testar com 5 deals conhecidos

```bash
cd /Users/IronMascarenhas_1/Projects/ix.BLZ-S(DS+UTM)
python -c "
from pd_api import get_deal, get_person
from dealscore.deal_score import compute_deal_score, FIELD_IDS
for did in [DEAL1, DEAL2, DEAL3, DEAL4, DEAL5]:
    d = get_deal(did)
    pid = (d.get('person_id') or {}).get('value')
    p = get_person(pid) if pid else {}
    s = compute_deal_score(d, p or {}, FIELD_IDS)
    print(f'Deal {did}: score={s.total} parts={s.parts}')
"
```

---

## Fase 2 — Migrar para API v2

Em `pd_api.py`:
- `BASE_URL_V2 = "https://api.pipedrive.com/api/v2"`
- Novos wrappers: `get_deal_v2()`, `update_deal_v2()`, `get_person_v2()`
- Manter v1 para: notes, products (sem suporte v2 completo)
- Cursor pagination em batch scripts (v2 usa `cursor` em vez de `start`)
- `include_fields=activities_count,products_count` no GET deal

Economia: PATCH deal 10→5 tokens, GET deal 2→1 token.

---

## Fase 3 — Auto-Produtos

Em `product_match.py` + `scripts/batch_enrich.py`:
- Se `products_count > 0` → NÃO mexer (vendedor ajustou)
- Se `products_count == 0` → POST bulk com Setup (one-time) + Mensalidade (monthly, 12 ciclos)
- Preços dos prints reais: Setup Premium R$5900, Mensalidade R$749-R$849
- Alinhar SETUP_TIERS e MENSALIDADE_TIERS com dados recentes

---

## Fase 4 — Rodar Batch

```bash
# Opção 1: rodar tudo (para no budget limit, resume amanhã)
python scripts/batch_enrich.py all

# Opção 2: limpar duplicatas primeiro
python scripts/clean_duplicate_notes.py all
```

O script tem:
- Budget tracking (~54 tokens/deal estimado, para em ~1.100 deals/dia)
- Resume: salva progresso em `scripts/.batch_progress.txt`
- Sort: mais recente → mais antigo
- Rate limit: 0.5s entre deals

---

## Estrutura de Arquivos Chave

```
dealscore/deal_score_rules.py    ← pesos e constantes do DealScore
dealscore/deal_score.py          ← engine de cálculo (compute_deal_score)
pd_api.py                        ← wrapper Pipedrive API (v1 + rate limit)
main.py                          ← Flask app + webhook + emoji tiers
notes_builder.py                 ← Rich Notes HTML builder
scripts/batch_enrich.py          ← batch processor (otimizado, com resume)
scripts/clean_duplicate_notes.py ← limpeza de notas duplicadas
product_match.py                 ← tiers de produto por DealScore
ltv.py                           ← cálculo LTV = Setup + (Mens × Tenure)
mappings.py                      ← field keys Pipedrive
parsers.py                       ← parse_meta_campaign (UTM → campos isolados)
_docs/deal_score_metodologia.md  ← FONTE DE VERDADE do DealScore
_docs/_JOBS/jobs.db              ← SQLite com todas as tarefas
_docs/_JOBS/JOBS.md              ← espelho legível do jobs.db
JOBS.md                          ← stub raiz apontando para _docs/_JOBS/
```

---

## Decisões Pendentes do Operador

1. **Emojis**: 🧊👀⚡🔥 (doc, 4 faixas) ou 🪨🌱🌿🌳🍀 (código, 5 faixas)?
2. **Site scores**: Doc principal diz +10/-10, update v2026-02-11 diz +15/-15. Qual prevalece?
3. **Preços produtos**: Alinhar com deals won recentes? Os tiers R$990/3500/5900 estão corretos?
4. **Person matching**: Buscar pessoa por email/org para deals órfãos agora ou backlog?

---

## Restrições

- NUNCA sobrescrever campos preenchidos pelo vendedor (LTV, Tenure, produtos)
- NUNCA rodar múltiplas instâncias batch (causa 429 e block)
- Respeitar rate limit: 0.5s entre deals, fail-fast se daily limit
- Preservar seção manual das Rich Notes (antes do `<hr>`)
- Manter compatibilidade com webhook handler (main.py)
- Diretório temporário: sempre `./tmp/` (nunca `/tmp/`)
