"""Pusher: cria/atualiza Person + Deal no Agendor a partir do dict normalizado.

Fluxo:
1. Dedup via store.already_ingested(provider, lead_id)
2. Busca person por email (search_person_by_email)
3. Se existir → reusa; senão → create_organization (se houver company) + create_person
4. create_deal_for_person — stage padrão "Leads"
5. Adiciona note com origem (form, ad, campaign, raw fields)
6. Registra em store + dispara fire_funnel_event (status_open / stage_leads)
"""
from __future__ import annotations
import os
import json
from typing import Any

from . import store


# Stage IDs do Agendor BKP (vide conversions.py STAGE_EVENT_MAP)
STAGE_LEADS = int(os.environ.get("AGENDOR_STAGE_LEADS", "3735676"))


def _safe(call, *a, **kw):
    try:
        return call(*a, **kw)
    except Exception as e:
        return {"_error": str(e)}


def _build_person_payload(norm: dict, org_id: int | None) -> dict:
    contact: dict = {}
    if norm.get("email"):
        contact["email"] = norm["email"]
    if norm.get("phone"):
        ph = norm["phone"]
        # tenta whatsapp + mobile
        contact["whatsapp"] = ph
        contact["mobile"]   = ph
    p: dict = {
        "name": norm.get("name") or norm.get("email") or f"Lead {norm.get('lead_id')}",
    }
    if contact:
        p["contact"] = contact
    if org_id:
        p["organization"] = org_id
    if norm.get("job"):
        p["jobTitle"] = norm["job"]
    return p


def _build_org_payload(norm: dict) -> dict:
    o: dict = {"name": norm.get("company") or "(empresa não informada)"}
    addr: dict = {}
    if norm.get("city"):  addr["city"]  = norm["city"]
    if norm.get("state"): addr["state"] = norm["state"]
    if norm.get("zip"):   addr["postalCode"] = norm["zip"]
    if addr:
        o["address"] = addr
    return o


def _build_deal_payload(norm: dict) -> dict:
    src = norm.get("source_meta", {})
    title = (norm.get("name") or "Lead") + f" — {src.get('campaign_name') or src.get('platform') or 'Form'}"
    return {
        "title": title,
        "dealStage": STAGE_LEADS,
        "dealStatusText": "ongoing",
    }


def _note_body(norm: dict, provider: str) -> str:
    src = norm.get("source_meta") or {}
    raw = norm.get("raw_fields") or {}
    lines = [
        f"📥 Lead recebido via {provider.upper()}",
        f"Lead ID: {norm.get('lead_id')}",
        f"Form ID: {src.get('form_id')}",
    ]
    if src.get("campaign_name"):
        lines.append(f"Campanha: {src.get('campaign_name')} ({src.get('campaign_id')})")
    if src.get("ad_name"):
        lines.append(f"Anúncio: {src.get('ad_name')} ({src.get('ad_id')})")
    if src.get("platform"):
        lines.append(f"Plataforma: {src.get('platform')}")
    if src.get("gcl_id"):
        lines.append(f"GCLID: {src.get('gcl_id')}")
    if raw:
        lines.append("")
        lines.append("Campos enviados:")
        for k, v in raw.items():
            lines.append(f"  • {k}: {v}")
    return "\n".join(lines)


def push_to_agendor(norm: dict, provider: str) -> dict:
    """Idempotente. Retorna {ok, status, person_id, deal_id, error?}."""
    lead_id = str(norm.get("lead_id") or "")
    form_id = (norm.get("source_meta") or {}).get("form_id")

    # 1. Dedup
    prev = store.already_ingested(provider, lead_id)
    if prev and prev.get("status") == "ok":
        return {"ok": True, "status": "duplicate",
                "person_id": prev.get("agendor_person_id"),
                "deal_id":   prev.get("agendor_deal_id"),
                "lead_id":   lead_id}

    # Imports atrasados pra evitar ciclo no boot
    from agendor_api import (
        create_organization, create_person, create_deal_for_person,
        search_person_by_email, add_note,
    )
    try:
        from conversions import fire_funnel_event
    except Exception:
        fire_funnel_event = None

    try:
        # 2. Procura person existente
        person = None
        if norm.get("email"):
            existing = search_person_by_email(norm["email"])
            if existing:
                person = existing

        # 3. Cria org se necessário
        org_id = None
        if not person and norm.get("company"):
            org_resp = _safe(create_organization, _build_org_payload(norm))
            if isinstance(org_resp, dict):
                org_data = org_resp.get("data") or org_resp
                org_id = (org_data or {}).get("id")

        # 4. Cria person se ainda não existe
        if not person:
            p_resp = _safe(create_person, _build_person_payload(norm, org_id))
            if isinstance(p_resp, dict) and p_resp.get("_error"):
                store.record(provider, lead_id, form_id=form_id, status="error",
                             error=f"create_person: {p_resp['_error']}", payload=norm)
                return {"ok": False, "error": p_resp["_error"], "step": "create_person"}
            person = (p_resp or {}).get("data") or p_resp or {}

        person_id = person.get("id")
        if not person_id:
            store.record(provider, lead_id, form_id=form_id, status="error",
                         error="person_id ausente após create/search", payload=norm)
            return {"ok": False, "error": "person_id ausente"}

        # 5. Cria deal
        d_resp = _safe(create_deal_for_person, person_id, _build_deal_payload(norm))
        if isinstance(d_resp, dict) and d_resp.get("_error"):
            store.record(provider, lead_id, form_id=form_id, status="error",
                         agendor_person_id=person_id,
                         error=f"create_deal: {d_resp['_error']}", payload=norm)
            return {"ok": False, "error": d_resp["_error"], "step": "create_deal",
                    "person_id": person_id}
        deal = (d_resp or {}).get("data") or d_resp or {}
        deal_id = deal.get("id")

        # 6. Note com origem
        if deal_id:
            _safe(add_note, deal_id, _note_body(norm, provider), 1)

        # 7. Registra
        store.record(provider, lead_id, form_id=form_id,
                     agendor_person_id=person_id, agendor_deal_id=deal_id,
                     status="ok", payload=norm)

        # 8. Dispara conversões (Lead = stage Leads)
        if fire_funnel_event and deal_id:
            try:
                deal_full = {**deal, "id": deal_id, "value": 0,
                             "fbclid": (norm.get("raw_fields") or {}).get("fbclid"),
                             "gclid":  (norm.get("source_meta") or {}).get("gcl_id"),
                             "organization": org_id}
                fire_funnel_event(f"stage_{STAGE_LEADS}", deal_full,
                                  person={"name": norm.get("name"),
                                          "email": norm.get("email"),
                                          "phone": norm.get("phone")})
            except Exception:
                pass

        return {"ok": True, "status": "created",
                "person_id": person_id, "deal_id": deal_id, "lead_id": lead_id}

    except Exception as e:
        store.record(provider, lead_id, form_id=form_id, status="error",
                     error=str(e), payload=norm)
        return {"ok": False, "error": str(e)}
