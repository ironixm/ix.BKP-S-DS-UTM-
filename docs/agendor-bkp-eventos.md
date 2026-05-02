# BKP — Mapeamento de Fases × Eventos (Meta / GA4 / Google Ads)

> **Fonte de verdade.** Se a planilha do squad mudar, atualize aqui e em [`conversions.py`](../conversions.py) (`STAGE_EVENT_MAP`).

## Funil Bankper (Agendor — Funnel "Funil de Vendas", id=713891)

| Nome em Relatórios | ID interno | Agendor Stage (id) | Agendor Status | Meta Ads | GA4 | Google Ads (env) |
|---|---|---|---|---|---|---|
| **Visitantes** | 0 | — | — | `PageView` + `ViewContent` | `page_view` | `page_view` |
| **Leads** | 1 | `3735676` Leads | `ongoing=1` | `Lead` | `generate_lead` | `generate_lead` (sem env ainda) |
| **MQL** | 3 | `2914195` Contato 1 (MQL) | `ongoing=1` | `CompleteRegistration` | `qualify_lead` | `GADS_CONV_DEMO_AGENDADA` |
| **SQL** | 4 | `2914196` Contato 2 (SQL) | `ongoing=1` | `SubmitApplication` | `working_lead` | `GADS_CONV_NEGOCIACAO_INICIADA` |
| **OPPs** | 5 | `2914197` Apresentação (OPTY) | `ongoing=1` | `Schedule` | `schedule` | `GADS_CONV_DEMO_AGENDADA` (offline reuse) |
| **Negociação** | 6 | `2914198` Fechamento (Negociação) | `ongoing=1` | `Proposal` (custom) | `view_proposal` | `GADS_CONV_NEGOCIACAO_INICIADA` (offline reuse) |
| **Fechamento (WON)** | 6w | qualquer stage | `won=2` | `Purchase` (com `value`+`currency`) | `purchase` | `GADS_CONV_CONVERTED_LEAD` |
| **Perdido** | 7 | qualquer stage | `lost=3` | `Lost` (custom — só análise, NÃO primary) | `disqualify_lead` | — |

### Critério Won/Lost
- WON pode ser dado em **qualquer etapa** do pipeline.
- Sempre que `dealStatus.id == 2` (won) → dispara `Purchase` independente da stage.
- Sempre que `dealStatus.id == 3` (lost) → dispara `Lost` (não-primary).

### Campos obrigatórios por fase (DealScore alternativo)
Cada avanço de fase exige campos adicionais (ou DealScore mínimo):
- **MQL:** Cargo + Empresa + Site + Segmento OU `score>50`
- **SQL:** + Funcionários + Faturamento OU `score>70`
- **OPPs:** + Valor do Deal assertivo OU `score>80`
- **Negociação:** + Dados da proposta OU `score>90`
- **Won (auto-mark):** `score>95`

## Webhooks Agendor — endpoints

A Agendor envia **só `{"data": {...deal...}}`** no body, sem indicar qual evento disparou. Por isso usamos **um path por evento** — o Flask lê o tipo da URL.

URL pattern: `https://bkp.alx-i.com/webhook/agendor/<event>/`

Eventos registrados (13):
```
on_activity_created
on_organization_created  on_organization_updated  on_organization_deleted
on_person_created        on_person_updated        on_person_deleted
on_deal_created          on_deal_updated          on_deal_deleted
on_deal_stage_updated    on_deal_won              on_deal_lost
```

Mapeamento evento → trigger interno:
| Evento Agendor | Trigger | Ação |
|---|---|---|
| `on_deal_created` | `stage_{currStage}` (geralmente Lead) | Dispara Meta `Lead` + GA4 `generate_lead` |
| `on_deal_stage_updated` | `stage_{currStage}` | Dispara conforme STAGE_EVENT_MAP |
| `on_deal_won` | `status_won` | Dispara WON_EVENTS |
| `on_deal_lost` | `status_lost` | Dispara LOST_EVENTS |
| `on_deal_updated` | (ignorado) | Apenas log |
| Demais (org/person/activity) | (ignorado) | Apenas log |

## Snapshot — onde editar

Código:
- [`conversions.py`](../conversions.py) — `STAGE_EVENT_MAP`, `WON_EVENTS`, `LOST_EVENTS`
- [`main.py`](../main.py) → rota `/webhook/agendor/<event>/`
- [`agendor_api.py`](../agendor_api.py) → `ensure_webhooks(target_url_pattern)`

Doc complementar:
- [`docs/agendor-webhooks.md`](agendor-webhooks.md) — gestão de webhooks via API
