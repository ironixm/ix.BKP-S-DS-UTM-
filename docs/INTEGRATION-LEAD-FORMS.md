# Integração: Lead Forms (Meta + Google Ads) → Agendor

> **Módulo:** `modules/lead_forms/` — ingestão automática de leads de formulários
> instantâneos do Meta (Facebook/Instagram) e do Google Ads, criando Person + Deal
> no Agendor com origem rastreada (campanha, ad, plataforma).

## Arquitetura

```
Meta Lead Ads ─┐
               ├─→ /webhook/meta/leadgen ──┐
               │   (ou /madmode/api/meta/  ├─→ mapper.py ─→ pusher.py ─→ Agendor
               │   backfill para histórico)│      │            │   ├─ org (se company)
Google Ads ────┴─→ /webhook/gads/leadform ─┘      │            │   ├─ person (com contact)
   (Lead Form Extension webhook push)             │            │   ├─ deal (stage Leads)
                                                   ▼            │   └─ note (origem)
                                          store.py (SQLite)     │
                                          dedup por             ▼
                                          (provider, lead_id)   conversions.fire_funnel_event
                                                                (dispara Lead em Meta CAPI/GA4/GAds)
```

## Endpoints

### Públicos (webhooks — sem auth)

| Rota | Método | Função |
|------|--------|--------|
| `/webhook/meta/leadgen` | GET | Verificação Meta (hub.challenge) |
| `/webhook/meta/leadgen` | POST | Recebe ping leadgen, busca lead, push Agendor |
| `/webhook/gads/leadform` | POST | Recebe push do Google Ads Lead Form Extension |

### Admin (autenticados via `/madmode/login`)

| Rota | Método | Função |
|------|--------|--------|
| `/madmode/api/lead-forms/stats` | GET | Total processado por provider/status |
| `/madmode/api/lead-forms/recent` | GET | `?provider=meta&limit=50` — últimos leads |
| `/madmode/api/meta/forms` | GET | Lista formulários de lead da página |
| `/madmode/api/meta/backfill` | POST | `{form_id, since?, dry_run?}` — backfill retroativo |
| `/madmode/api/lead-forms/replay` | POST | `{provider, lead_id}` — reprocessa lead com erro |

## Variáveis de ambiente necessárias

| Var | Obrigatório | Descrição |
|-----|-------------|-----------|
| `META_LEADS_TOKEN` | **Sim (Meta)** | Page Access Token com escopos `pages_show_list`, `pages_read_engagement`, `leads_retrieval` |
| `META_PAGE_ID` | Recomendado | ID da página Facebook (se omitido, tenta descobrir via `/me/accounts`) |
| `META_WEBHOOK_VERIFY_TOKEN` | **Sim (Meta)** | String aleatória — usada no setup do webhook em developers.facebook.com |
| `META_APP_SECRET` | Opcional | Para validar `X-Hub-Signature-256` (recomendado em produção) |
| `GADS_WEBHOOK_KEY` | **Sim (GAds)** | Chave compartilhada — configurar no formulário Google Ads e enviada via `?key=` |
| `AGENDOR_TOKEN` | Sim | Já existente — usado pelo `agendor_api.py` |
| `AGENDOR_STAGE_LEADS` | Opcional | Default `3735676` — ID do stage "Leads" |
| `LEADFORMS_DB` | Opcional | Default `/data/leadforms.sqlite` — path do dedup store |

> **CRÍTICO:** o `META_ACCESS_TOKEN` que já temos no Coolify (System User do CAPI)
> tem APENAS o scope `read_ads_dataset_quality` — **não consegue ler leads**.
> Precisa gerar Page Access Token novo seguindo o passo-a-passo abaixo.

## Setup Meta Lead Ads — passo a passo

### 1. Gerar Page Access Token com scopes corretos

1. Acessar [developers.facebook.com](https://developers.facebook.com) → seu App → Tools → **Graph API Explorer**
2. Selecionar o App, escolher **User Token**
3. Adicionar permissions: `pages_show_list`, `pages_read_engagement`, `leads_retrieval`, `ads_management`
4. Clicar **Generate Access Token** → autorizar página BKP/Bankper
5. Trocar User Token por Page Token (long-lived) — endpoint:
   ```
   GET /me/accounts?access_token=<USER_TOKEN_LONG_LIVED>
   ```
6. Copiar `access_token` da página BKP → salvar como `META_LEADS_TOKEN` no Coolify

### 2. Configurar Webhook no App Meta

1. App → **Webhooks** → Adicionar produto **Page**
2. URL de callback: `https://bkp.alx-i.com/webhook/meta/leadgen`
3. Verify Token: usar valor de `META_WEBHOOK_VERIFY_TOKEN`
4. Subscrever campo: **leadgen**
5. Em **Subscribed apps** da página, conectar o app

### 3. Backfill de leads históricos (após token válido)

```bash
# 1. Listar formulários
curl -b cookies.txt https://bkp.alx-i.com/madmode/api/meta/forms

# 2. Dry-run (preview)
curl -b cookies.txt -X POST https://bkp.alx-i.com/madmode/api/meta/backfill \
  -H "Content-Type: application/json" \
  -d '{"form_id":"<FORM_ID>","since":"2026-01-01","dry_run":true}'

# 3. Execução real
curl -b cookies.txt -X POST https://bkp.alx-i.com/madmode/api/meta/backfill \
  -H "Content-Type: application/json" \
  -d '{"form_id":"<FORM_ID>","since":"2026-01-01"}'
```

## Setup Google Ads Lead Form

### 1. No Google Ads

1. Anúncio → **Lead form asset** → Editar
2. Em **Lead delivery options** → habilitar **Webhook integration**
3. URL: `https://bkp.alx-i.com/webhook/gads/leadform?key=<GADS_WEBHOOK_KEY>`
4. Key (campo): mesmo valor de `GADS_WEBHOOK_KEY`
5. Clicar **Send test data** — deve retornar 200

### 2. Validação

```bash
curl -b cookies.txt https://bkp.alx-i.com/madmode/api/lead-forms/stats
curl -b cookies.txt 'https://bkp.alx-i.com/madmode/api/lead-forms/recent?provider=gads&limit=20'
```

## Dedup e idempotência

- Tabela `leadform_ingested` em SQLite (`LEADFORMS_DB`)
- Chave única: `(provider, lead_id)`
- Ao receber webhook ou backfill, se o lead já foi processado com `status='ok'`,
  retorna `{status:'duplicate'}` sem chamar Agendor
- Status possíveis: `ok | error | duplicate | no_data | pending`

## Conversões disparadas após criar deal

Após criar Person+Deal no Agendor, `pusher.py` chama
`conversions.fire_funnel_event(f"stage_{STAGE_LEADS}", deal, person)` que dispara:
- **Meta CAPI**: evento `Lead`
- **GA4**: `generate_lead`
- **Google Ads**: `generate_lead`

Mais detalhes da matriz funil → eventos: ver `docs/FUNNEL-EVENTS.md` (BLZ).

## Arquivos do módulo

```
modules/lead_forms/
├── __init__.py        # exports public_bp, admin_bp
├── meta_client.py     # Graph API (list_pages, list_forms, list_leads, get_lead)
├── mapper.py          # field_data Meta + user_column_data GAds → dict normalizado
├── pusher.py          # cria org+person+deal+note no Agendor + dispara funnel event
├── store.py           # SQLite dedup (leadform_ingested)
└── routes.py          # blueprints public + admin
```

## Limitações conhecidas

1. **Token Meta atual não funciona** — precisa gerar Page Token com scopes (item 1)
2. **GAds não tem polling/backfill por API** — só webhook push. Leads anteriores ao
   setup do webhook são acessíveis somente via:
   - Download CSV manual em ads.google.com → upload via endpoint custom (TODO)
   - Reports API com `lead_form_submission_data` (TODO)
3. **Org sem CNPJ não enriquece** — ver job #60 (enrichment fallback por nome)
4. **Webhook Meta sem App Secret** opera em modo permissivo (qualquer signature aceita)
   — recomenda-se configurar `META_APP_SECRET` em produção

## Troubleshooting

```bash
# Ver últimos erros
curl -b cookies.txt 'https://bkp.alx-i.com/madmode/api/lead-forms/recent?limit=20' \
  | jq '.items[] | select(.status=="error") | {lead_id, error, received_at}'

# Reprocessar lead com erro
curl -b cookies.txt -X POST https://bkp.alx-i.com/madmode/api/lead-forms/replay \
  -H "Content-Type: application/json" \
  -d '{"provider":"meta","lead_id":"<LEAD_ID>"}'

# Logs do container
# Coolify → bkp-s → Logs
```
