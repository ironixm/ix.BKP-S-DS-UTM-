# Conversões — GA4 + Meta + Google Ads

> Referência única dos eventos disparados pelo `bzl.alx-i.com` ao longo do funil Pipedrive
> e do passo-a-passo para configurar Pmax/Smart Bidding usando esses sinais.

## Mapa de Eventos

| Pipedrive Stage | Nome do estágio | Meta CAPI | GA4 | Google Ads (offline) |
|---|---|---|---|---|
| 139 | Levantada de Mão | `Lead` | `generate_lead` | — (importar via GA4) |
| 13  | Contato 1 | `CompleteRegistration` | `qualify_lead` | — (importar via GA4) |
| 47  | Demo Agendada | `Schedule` | `schedule` | `Demo_Agendada` (CAPI direto + GA4) |
| 16  | Demo/Proposta enviada | `SubmitApplication` | `view_proposal` | — (importar via GA4) |
| 17  | Negociação | `Proposal` (custom) | `begin_checkout` | `Negociacao_Iniciada` (CAPI direto + GA4) |
| won  | Status Ganho | `Purchase` | `purchase` | `Converted_Lead` (CAPI direto + GA4) |
| lost | Status Perdido | `Lost` (custom) | `disqualify_lead` | — |

**Notas de design:**
- Cada estágio tem nome **único** em todos os canais → permite criar conversion goals separados
- Nomes GA4 alinhados à taxonomia Google (`schedule`, `begin_checkout`, `purchase`) → Pmax otimiza nativamente
- GAds via CAPI (real-time) **apenas para fundo de funil** (47/17/won) — para topo basta importar do GA4
- Meta `Proposal` e `Lost` são **custom events** (não padrão CAPI)

## Configuração GA4 → Google Ads → Pmax

Passos para a Pmax usar esses sinais como conversion goals:

### 1. GA4 — Marcar como conversão principal

`Admin → Eventos → Eventos recentes` → clicar na ⭐ ao lado de cada um:

- ⭐ `generate_lead`
- ⭐ `qualify_lead`
- ⭐ `schedule`
- ⭐ `view_proposal`
- ⭐ `begin_checkout`
- ⭐ `purchase`
- ⭐ `disqualify_lead` (opcional — sinal negativo)

### 2. GA4 — Vincular ao Google Ads

`Admin → Vinculações de produtos → Google Ads` → confirmar que a conta da Buzzlead está conectada (já deve estar). Se não, "Vincular" → selecionar conta MCC.

### 3. Google Ads — Importar conversões do GA4

`Ferramentas → Conversões → +Nova → Importar → Google Analytics 4 properties` → selecionar todas as 6 conversões marcadas → "Importar e continuar".

Resultado: aparecem em `Conversões` com origem `Google Analytics (GA4)` e categoria editável.

### 4. Google Ads — Categorizar conversões

| Conversão importada | Categoria recomendada | Inclui em "Conversões"? |
|---|---|---|
| `generate_lead` | Lead → Submit lead form | ✅ |
| `qualify_lead` | Lead → Qualified lead | ✅ |
| `schedule` | Lead → Book appointment | ✅ |
| `view_proposal` | Other (Lead → Request quote) | ⚠️ Secundária |
| `begin_checkout` | Purchase → Begin checkout | ✅ |
| `purchase` | Purchase → Purchase | ✅ (primária) |

### 5. Pmax — Conversion goals da campanha

`Campanha Pmax → Configurações → Conversion goals` → mudar de "Conta padrão" para **personalizada** → adicionar:

- **Conversion goal primário**: `purchase` (peso máximo)
- **Secundárias**: `schedule`, `begin_checkout`, `qualify_lead`, `generate_lead`

### 6. Smart Bidding — Estratégia

Sugestão para Pmax B2B com ciclo de vendas longo:
- **tCPA** durante warm-up (~21 dias) usando `schedule` como goal primário (mais frequente)
- Migrar para **tROAS** após acumular 30+ `purchase` (usa LTV real do CRM)

## Checagem de funcionamento

```bash
# Smoke test em qualquer estágio
curl -s -X POST "https://bzl.alx-i.com/webhook/pipedrive/?token=ix-sync" \
  -H "Content-Type: application/json" \
  -d '{"meta":{"action":"create","entity":"deal","version":"2.0"},
       "data":{"id":<DEAL_ID>,"stage_id":<STAGE>,"status":"open"},
       "previous":null}'
```

Resposta esperada:
```json
{
  "conversions": {
    "stage_47": {
      "ga4":  {"ok": true, "status": 204},
      "meta": {"ok": true, "status": 200},
      "gads": {"ok": true, "status": "uploaded"}
    }
  }
}
```

## Variáveis de ambiente (Coolify · `blz-s`)

- `META_PIXEL_ID`, `META_ACCESS_TOKEN`
- `GA4_MEASUREMENT_ID`, `GA4_API_SECRET`
- `GADS_CONV_DEMO_AGENDADA`, `GADS_CONV_NEGOCIACAO_INICIADA`, `GADS_CONV_CONVERTED_LEAD`
- `GADS_DEVELOPER_TOKEN`, `GADS_CUSTOMER_ID`, etc. (vide `conversions.py`)

## Histórico

- **2026-04-29 (V2.1)** — Quebra de `working_lead` em 3 eventos únicos (`schedule`, `view_proposal`, `begin_checkout`). Migração one-shot, sem dados a preservar.
- **2026-04-29** — `detect_triggers` passa a disparar em `create.deal`/`added.deal` (antes só `change.deal`).
- **2026-04-23** — V2.0 inicial (commit `4ded41b`): mapa original com colisão em `working_lead`.
