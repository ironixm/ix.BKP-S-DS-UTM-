# Agendor Webhooks — Guia para AGENTS (ix.BKP)

> **Fonte oficial:** https://ajuda.agendor.com.br/pt-BR/articles/6281963
> **Postman:** https://www.postman.com/grey-comet-695161/agendor-api (folder "Webhooks/Gatilhos")

## ⚠️ Importante

- O painel web do Agendor **NÃO tem mais** UI para criar/editar webhooks.
- A **única forma** de gerir webhooks é via API REST.
- O endpoint **NÃO está sob `/v3`** — fica na raiz: `https://api.agendor.com.br/integrations/subscriptions`.
- Auth: `Authorization: Token <AGENDOR_TOKEN>` (NÃO Bearer).
- 1 webhook = **1 evento** (não há array de eventos no POST). Para registrar N eventos → N requests.

## Endpoints

| Método | URL | Função |
|--------|-----|--------|
| `GET` | `/integrations/subscriptions` | Listar webhooks ativos |
| `POST` | `/integrations/subscriptions` | Criar webhook (`{"target_url": "...", "event": "on_xxx"}`) |
| `DELETE` | `/integrations/subscriptions/<id>` | Remover webhook |

## Eventos disponíveis (13)

```
on_activity_created
on_organization_created  on_organization_updated  on_organization_deleted
on_person_created        on_person_updated        on_person_deleted
on_deal_created          on_deal_updated          on_deal_deleted
on_deal_stage_updated    on_deal_won              on_deal_lost
```

## Privacidade

O webhook respeita o usuário dono do TOKEN. Se o token for de **ADMIN**, dispara para todas as entidades; se for **COLABORADOR**, só para as que ele enxerga.
→ Use sempre o token do usuário admin da conta.

## Uso no projeto BKP

Helpers em [`agendor_api.py`](../agendor_api.py):

```python
from agendor_api import (
    list_webhooks, create_webhook, delete_webhook, ensure_webhooks,
    AGENDOR_EVENTS,
)

# Idempotente — garante todos os 13 eventos para o endpoint do BKP:
ensure_webhooks("https://bkp.alx-i.com/webhook/agendor/")

# Listar:
for w in list_webhooks():
    print(w["id"], w["event"], w["target_url"])

# Remover por id:
delete_webhook(12788)
```

## CLI (curl)

```bash
TOK="$AGENDOR_TOKEN"

# Listar
curl -sS -H "Authorization: Token $TOK" \
  https://api.agendor.com.br/integrations/subscriptions

# Criar (exemplo: deal criado)
curl -sS -X POST https://api.agendor.com.br/integrations/subscriptions \
  -H "Authorization: Token $TOK" -H "Content-Type: application/json" \
  -d '{"target_url":"https://bkp.alx-i.com/webhook/agendor/","event":"on_deal_created"}'

# Deletar
curl -sS -X DELETE -H "Authorization: Token $TOK" \
  https://api.agendor.com.br/integrations/subscriptions/12788
```

## Estado atual (BKP — 2026-05-02)

13 webhooks ativos apontando para `https://bkp.alx-i.com/webhook/agendor/` (IDs 12788–12800).
Handler em [`main.py`](../main.py) → rota `/webhook/agendor/` → normaliza payload e grava em `events` (PG) com `source='agendor'`.

Health check em `/madmode/api/overview` lê `events` últimas 24h com `source='agendor'`.
