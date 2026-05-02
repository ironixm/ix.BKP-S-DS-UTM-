"""Adapter para Agendor v3 REST com a MESMA assinatura de pd_api.py.

Mapeamento Pipedrive → Agendor:
  person/{id}        ↔ people/{id}
  organization/{id}  ↔ organizations/{id}
  deal/{id}          ↔ deals/{id}
  deal_notes         ↔ deals/{id}/activities (filtradas por type=note)

Auth: Authorization: Token <AGENDOR_TOKEN>
Base: https://api.agendor.com.br/v3
"""
from __future__ import annotations
import os, time, requests

BASE_URL = os.environ.get("AGENDOR_BASE_URL", "https://api.agendor.com.br/v3").rstrip("/")
TOKEN = os.environ.get("AGENDOR_TOKEN", "").strip()

SESSION = requests.Session()
if TOKEN:
    SESSION.headers.update({"Authorization": f"Token {TOKEN}",
                            "Content-Type": "application/json"})

_last_t = 0.0
_MIN_INT = 0.25  # ~4 req/s


def _request(path: str, params=None, method="GET", json=None):
    global _last_t
    elapsed = time.time() - _last_t
    if elapsed < _MIN_INT:
        time.sleep(_MIN_INT - elapsed)
    for attempt in range(4):
        _last_t = time.time()
        r = SESSION.request(method, f"{BASE_URL}{path}",
                            params=params, json=json, timeout=20)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 5))
            print(f"  ⏳ 429 Agendor — aguardando {wait}s")
            time.sleep(min(wait + 1, 60)); continue
        if r.status_code == 404:
            return None
        r.raise_for_status()
        if r.status_code == 204 or not r.text:
            return {}
        return r.json()
    r.raise_for_status()
    return r.json()


# =====================================================
# NORMALIZAÇÃO Agendor → formato esperado pelo BLZ
# =====================================================

def _normalize_person(p: dict | None) -> dict | None:
    """Agendor people → Pipedrive-like person dict (email/phone arrays)."""
    if not p: return None
    emails, phones = [], []
    for e in (p.get("contact") or {}).get("email") or []:
        if isinstance(e, dict): emails.append({"value": e.get("email") or e.get("value") or ""})
        elif isinstance(e, str): emails.append({"value": e})
    if (p.get("contact") or {}).get("whatsapp"):
        phones.append({"value": p["contact"]["whatsapp"]})
    if (p.get("contact") or {}).get("mobile"):
        phones.append({"value": p["contact"]["mobile"]})
    return {
        "id": p.get("id"),
        "name": p.get("name") or "",
        "email": emails,
        "phone": phones,
        "_raw_agendor": p,
    }


def _normalize_org(o: dict | None) -> dict | None:
    if not o: return None
    return {
        "id": o.get("id"),
        "name": o.get("name") or "",
        "_raw_agendor": o,
    }


def _normalize_deal(d: dict | None) -> dict | None:
    if not d: return None
    stage = d.get("dealStage") or {}
    person = d.get("people") or [None]
    if isinstance(person, list):
        person = person[0] if person else None
    org = d.get("organization") or {}
    return {
        "id": d.get("id"),
        "title": d.get("description") or d.get("title") or "",
        "value": d.get("value") or 0,
        "currency": "BRL",
        "status": _map_status(d.get("status")),
        "stage_id": stage.get("id") if isinstance(stage, dict) else None,
        "stage_name": stage.get("name") if isinstance(stage, dict) else None,
        "person_id": (person or {}).get("id") if isinstance(person, dict) else None,
        "person_name": (person or {}).get("name") if isinstance(person, dict) else None,
        "org_id": org.get("id") if isinstance(org, dict) else None,
        "org_name": org.get("name") if isinstance(org, dict) else None,
        "_raw_agendor": d,
    }


def _map_status(s):
    """Agendor status → pipedrive-like."""
    if isinstance(s, dict):
        s = s.get("name") or s.get("text") or ""
    s = (s or "").lower()
    if "ganh" in s or "won" in s: return "won"
    if "perd" in s or "lost" in s: return "lost"
    return "open"


# =====================================================
# PERSON
# =====================================================

def get_person(person_id):
    data = _request(f"/people/{person_id}")
    return _normalize_person((data or {}).get("data") or data)


def update_person(person_id, payload):
    return _request(f"/people/{person_id}", method="PUT", json=payload)


# =====================================================
# ORGANIZATION
# =====================================================

def get_organization(org_id):
    data = _request(f"/organizations/{org_id}")
    return _normalize_org((data or {}).get("data") or data)


def update_organization(org_id, payload):
    return _request(f"/organizations/{org_id}", method="PUT", json=payload)


# =====================================================
# DEAL
# =====================================================

def get_deal(deal_id):
    data = _request(f"/deals/{deal_id}")
    return _normalize_deal((data or {}).get("data") or data)


def update_deal(deal_id, payload):
    """Aceita payload Pipedrive-like e converte para Agendor."""
    ag_payload = {}
    if "title" in payload:        ag_payload["description"] = payload["title"]
    if "value" in payload:        ag_payload["value"] = payload["value"]
    if "stage_id" in payload:     ag_payload["dealStage"] = payload["stage_id"]
    if "status" in payload:
        st = payload["status"]
        ag_payload["status"] = "won" if st == "won" else ("lost" if st == "lost" else "ongoing")
    # Custom fields: caller deve passar ag_payload["customFields"] explicitamente
    if "customFields" in payload: ag_payload["customFields"] = payload["customFields"]
    return _request(f"/deals/{deal_id}", method="PUT", json=ag_payload)


def create_organization(payload: dict) -> dict | None:
    """POST /organizations. payload: {name, cnpj?, website?, ...}"""
    return _request("/organizations", method="POST", json=payload)


def create_person(payload: dict) -> dict | None:
    """POST /people. payload: {name, organization?, contact: {email, mobile, whatsapp, work}, ...}"""
    return _request("/people", method="POST", json=payload)


def create_deal_for_person(person_id: int, payload: dict) -> dict | None:
    """POST /people/{personId}/deals. payload: {title, value?, dealStage?, dealStatusText?, ...}"""
    return _request(f"/people/{person_id}/deals", method="POST", json=payload)


def search_person_by_email(email: str) -> dict | None:
    """Busca person por email. Retorna primeiro match ou None."""
    if not email:
        return None
    try:
        data = _request("/people", params={"contact_email": email, "per_page": 5}) or {}
        items = data.get("data") or []
        return items[0] if items else None
    except Exception:
        return None


def get_deals_by_filter(filter_id, start=0, limit=100):
    """Agendor não tem 'filters' como Pipedrive. Retorna deals paginados."""
    return get_deals(start=start, limit=limit)


def get_deals(start=0, limit=100, status="all_not_deleted", sort=None):
    page = (start // limit) + 1 if limit else 1
    params = {"page": page, "per_page": limit}
    data = _request("/deals", params=params) or {}
    items = data.get("data") or data.get("deals") or []
    return {
        "data": [_normalize_deal(d) for d in items],
        "additional_data": {"pagination": {
            "more_items_in_collection": bool((data.get("pagination") or {}).get("next")),
            "next_start": start + len(items),
        }},
    }


def get_deals_count_by_filter(filter_id):
    data = _request("/deals", params={"page": 1, "per_page": 1}) or {}
    return (data.get("pagination") or {}).get("total") or 0


# =====================================================
# NOTES (Activities type=note no Agendor)
# =====================================================

def get_deal_notes(deal_id):
    data = _request(f"/deals/{deal_id}/activities") or {}
    items = data.get("data") or []
    notes = []
    for a in items:
        if (a.get("activityType") or {}).get("name") == "note" or a.get("type") == "note":
            notes.append({
                "id": a.get("id"),
                "content": a.get("text") or a.get("description") or "",
                "add_time": a.get("createdAt") or "",
                "user": (a.get("user") or {}).get("name") or "",
            })
    return notes


def add_note(deal_id, content, pinned=1):
    body = {"text": content, "type": "note"}
    return _request(f"/deals/{deal_id}/activities", method="POST", json=body)


def update_note(note_id, content):
    return _request(f"/activities/{note_id}", method="PUT", json={"text": content})


def delete_note(note_id):
    return _request(f"/activities/{note_id}", method="DELETE")


def dedup_auto_notes_for_deal(deal_id, keep: str = "newest") -> dict:
    """Stub: Agendor activities são imutáveis em geral. Retorna no-op."""
    return {"deleted": 0, "kept": 0, "skipped": True, "reason": "agendor-noop"}


# =====================================================
# PRODUCTS (Agendor: produtos vinculados a deal)
# =====================================================

def get_products(limit=100):
    data = _request("/products", params={"per_page": limit}) or {}
    return {"data": data.get("data") or []}


def search_product(term):
    data = _request("/products", params={"q": term, "per_page": 20}) or {}
    return {"data": data.get("data") or []}


def get_deal_products(deal_id):
    data = _request(f"/deals/{deal_id}/products") or {}
    return {"data": data.get("data") or []}


def add_product_to_deal(deal_id, product_id, item_price, quantity=1):
    body = {"product": product_id, "value": item_price, "quantity": quantity}
    return _request(f"/deals/{deal_id}/products", method="POST", json=body)


# =====================================================
# WEBHOOKS / SUBSCRIPTIONS
# Endpoint: https://api.agendor.com.br/integrations/subscriptions
# (NÃO está sob /v3 — usa root da API)
# Doc: https://ajuda.agendor.com.br/pt-BR/articles/6281963
# =====================================================

WEBHOOKS_URL = "https://api.agendor.com.br/integrations/subscriptions"

AGENDOR_EVENTS = [
    "on_activity_created",
    "on_organization_created", "on_organization_updated", "on_organization_deleted",
    "on_person_created", "on_person_updated", "on_person_deleted",
    "on_deal_created", "on_deal_updated", "on_deal_deleted",
    "on_deal_stage_updated", "on_deal_won", "on_deal_lost",
]


def list_webhooks() -> list:
    """GET /integrations/subscriptions — retorna lista de webhooks ativos."""
    r = SESSION.get(WEBHOOKS_URL, timeout=20)
    r.raise_for_status()
    return (r.json() or {}).get("data") or []


def create_webhook(target_url: str, event: str) -> dict:
    """POST /integrations/subscriptions — cria 1 webhook para 1 evento."""
    if event not in AGENDOR_EVENTS:
        raise ValueError(f"Evento inválido: {event}. Use um de {AGENDOR_EVENTS}")
    r = SESSION.post(WEBHOOKS_URL, json={"target_url": target_url, "event": event}, timeout=20)
    r.raise_for_status()
    return (r.json() or {}).get("data") or {}


def delete_webhook(webhook_id: int) -> bool:
    """DELETE /integrations/subscriptions/<id>."""
    r = SESSION.delete(f"{WEBHOOKS_URL}/{int(webhook_id)}", timeout=20)
    return r.status_code in (200, 204)


def ensure_webhooks(target_url: str, events: list = None, per_event_path: bool = True) -> dict:
    """Idempotente: garante que existe 1 webhook por evento.

    Se per_event_path=True (default), cada evento recebe URL própria:
    `<target_url>/<event>/`. Isso permite que o handler descubra o tipo do
    evento via path (Agendor não envia 'event' no body).

    Retorna {created: [...], existing: [...], deleted_old: [...]}.
    """
    events = events or AGENDOR_EVENTS
    base = target_url.rstrip("/")
    existing = list_webhooks()
    have = {(w.get("event"), w.get("target_url")) for w in existing}
    created, kept, deleted = [], [], []
    for ev in events:
        url = f"{base}/{ev}/" if per_event_path else f"{base}/"
        if (ev, url) in have:
            kept.append(ev)
        else:
            created.append(create_webhook(url, ev))
        # Remove versões antigas do mesmo evento que não batam com a URL nova
        for w in existing:
            if w.get("event") == ev and w.get("target_url") != url and base in (w.get("target_url") or ""):
                if delete_webhook(w["id"]):
                    deleted.append(w["id"])
    return {"created": created, "existing": kept, "deleted_old": deleted}
