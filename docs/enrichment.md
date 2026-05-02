# Enrichment — ix.BKP/BLZ

> Port em Python do `enrichmentService.js` original (BKP-Leads-Sync v2).
> Mesmo pipeline rodando em **ambos** projetos (BKP/Agendor e BLZ/Pipedrive)
> via *adapter pattern*.

## Pipeline

| Etapa | Fonte | Custo | ENV para desligar |
|-------|-------|-------|-------------------|
| 1. CNPJ chain | BrasilAPI → MinhaReceita → ReceitaWS | free | `ENRICHMENT_BRASILAPI_ENABLED=OFF` etc. |
| 2. CNPJ por scraping | requests no website da org | free | `ENRICHMENT_SITE_SCRAPING_ENABLED=OFF` |
| 3. Email checks (commercial/disposable) | listas locais | free | — |
| 4. Disposable email API | NinjaPear/Nubela | free | `ENRICHMENT_DISPOSABLE_EMAIL_ENABLED=OFF` |
| 5. Company logo | NinjaPear `/company/logo` | free | `ENRICHMENT_COMPANY_LOGO_ENABLED=OFF` |
| 6. Company details | NinjaPear `/company/details` | **2 cred** | `ENRICHMENT_COMPANY_DETAILS_ENABLED=OFF` |
| 7. WhatsApp Business | scraping wa.me | free | `ENRICHMENT_WHATSAPP_ENABLED=OFF` |
| 8. LinkedIn | Google CSE search | free* | `ENRICHMENT_LINKEDIN_ENABLED=OFF` |

\* Google CSE: 100 queries/dia gratuitas.

## ENVs obrigatórias / opcionais

```env
# Master switch (default ON)
ENRICHMENT_ENABLED=ON

# NinjaPear (Nubela/Proxycurl) — obrigatória para etapas 4/5/6
NINJAPEAR_API_KEY=...

# Google CSE — opcional, para fallback LinkedIn
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_CX=b799e5585cbd040d4
```

Sem `NINJAPEAR_API_KEY`, etapas que dependem dela retornam
`{"ok": false, "reason": "missing_api_key"}` e o pipeline continua.

## Triggers (BKP — Agendor)

Configurado em `main.py` no handler `/webhook/agendor/<event>/`:

| Webhook Agendor | Ação |
|-----------------|------|
| `on_organization_created` | dispatch `enrich_organization(org_id)` async |
| `on_organization_updated` | idem (idempotente; só preenche vazios) |
| `on_person_created` | dispatch `enrich_person(person_id)` async |
| `on_person_updated` | idem |

Execução em thread daemon — webhook responde 202 imediatamente.

## API admin

```
POST /madmode/api/enrichment/run
  { "entity": "organization|person", "id": <int>, "mode": "auto|force" }

GET  /madmode/api/enrichment/stats?hours=168
  → totals por source/entity, taxa sucesso, créditos NP estimados, últimas 50 runs
```

## UI

Aba `✨ Enrichment` no MadMode (`/madmode/enrichment`):
- KPIs 7d (runs, sucesso, créditos NP)
- Form de execução manual
- Tabela das últimas 50 execuções (fontes / campos coletados / status apply)

## Adapters disponíveis

- `enrichment.adapter_agendor` — campos custom Agendor BKP
- `enrichment.adapter_pipedrive` — TODO no fork BLZ

Cada adapter implementa:
```python
get_org(id) -> dict | None
org_cnpj(org) -> str | None
update_org_with_enrichment(id, enriched_data) -> dict
get_person_data(id) -> dict | None
update_person_with_enrichment(id, enriched_data) -> dict
```

## Observabilidade

Cada execução grava no events.log:
```json
{ "event": "enrichment_org",
  "payload": { "entity_id": 123, "sources": ["brasilapi","ninjapear_logo"],
               "fields_collected": [...], "apply": {"applied":[...]},
               "duration_ms": 2348, "ok": true } }
```

`enrichment_person` análogo. Stats no `/madmode/api/enrichment/stats`.

## Limites e cuidados

- **BrasilAPI**: ~10 req/s sustentado. OK para webhook em rajada.
- **MinhaReceita**: sem rate-limit declarado — comporta-se bem.
- **ReceitaWS**: 3 req/min free; é o **último fallback** por isso.
- **NinjaPear**: cada `/company/details` = 2 créditos. Monitore no painel.
- **Cache local** (1h) de CNPJs já buscados, reduz hits redundantes.
- **Idempotência**: modo `auto` nunca sobrescreve campo preenchido.
