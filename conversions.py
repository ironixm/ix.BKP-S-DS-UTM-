# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Conversions – V2.0.0                           │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-21 - 17:35         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ conversions.py                                 │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V2.0.0 - Full funnel events: Meta+GA4+GAds   │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Disparo de eventos de funil para Meta CAPI, GA4 Measurement Protocol
e Google Ads Offline Conversions.

Mapeamento de estágios Pipedrive → eventos:

  Stage 139 (Levantada Mão)  → Meta:Lead              GA4:generate_lead
  Stage 13  (Contato 1)      → Meta:CompleteRegistration  GA4:qualify_lead
  Stage 47  (Agendado)       → Meta:Schedule           GA4:schedule        GAds:Demo_Agendada
  Stage 16  (Demo/Proposta)  → Meta:SubmitApplication  GA4:view_proposal
  Stage 17  (Negociação)     → Meta:Proposal(custom)   GA4:begin_checkout  GAds:Negociacao_Iniciada
  Status won                 → Meta:Purchase           GA4:purchase        GAds:Converted_Lead
  Status lost                → Meta:Lost(custom)       GA4:disqualify_lead

Env vars:
  META_PIXEL_ID, META_ACCESS_TOKEN          — Meta CAPI
  GA4_MEASUREMENT_ID, GA4_API_SECRET        — GA4 Measurement Protocol
  GOOGLE_ADS_CUSTOMER_ID, GOOGLE_ADS_DEV_TOKEN,
  GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET,
  GOOGLE_ADS_REFRESH_TOKEN                  — Google Ads Offline (amanhã)
  GADS_CONV_DEMO_AGENDADA                   — Conversion Action ID
  GADS_CONV_NEGOCIACAO_INICIADA             — Conversion Action ID
  GADS_CONV_CONVERTED_LEAD                  — Conversion Action ID
"""
from __future__ import annotations

import os
import json
import time
import hashlib
import requests
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# MAPEAMENTO DE ESTÁGIOS → EVENTOS
# ─────────────────────────────────────────────────────────────

# Cada entrada: stage_id → {meta, ga4, gads}
# meta: None = não dispara | str = nome do evento | (str, True) = evento custom
# gads: None = não dispara | str = env var com o Conversion Action ID
STAGE_EVENT_MAP: dict[int, dict] = {
    139: {"meta": "Lead",                     "ga4": "generate_lead",  "gads": None},
    13:  {"meta": "CompleteRegistration",     "ga4": "qualify_lead",   "gads": None},
    47:  {"meta": "Schedule",                 "ga4": "schedule",       "gads": "GADS_CONV_DEMO_AGENDADA"},
    16:  {"meta": "SubmitApplication",        "ga4": "view_proposal",  "gads": None},
    17:  {"meta": ("Proposal", True),         "ga4": "begin_checkout", "gads": "GADS_CONV_NEGOCIACAO_INICIADA"},
}

# Eventos de status won/lost
WON_EVENTS  = {"meta": "Purchase",         "ga4": "purchase",         "gads": "GADS_CONV_CONVERTED_LEAD"}
LOST_EVENTS = {"meta": ("Lost", True),     "ga4": "disqualify_lead",  "gads": None}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


def _normalize_phone(phone: str) -> str:
    """Remove formatação e garante prefixo 55 para BR."""
    clean = "".join(c for c in phone if c.isdigit())
    if len(clean) in (10, 11):
        clean = "55" + clean
    return clean


def _extract_person_data(person: dict | None) -> dict:
    """Extrai email, phone, nome do objeto person do Pipedrive."""
    if not person:
        return {}
    result = {}
    emails = person.get("email") or []
    if emails:
        e = emails[0]
        result["email"] = (e.get("value") if isinstance(e, dict) else e) or ""
    phones = person.get("phone") or []
    if phones:
        p = phones[0]
        result["phone"] = (p.get("value") if isinstance(p, dict) else p) or ""
    result["name"] = person.get("name") or ""
    return result


# ─────────────────────────────────────────────────────────────
# META CONVERSIONS API (CAPI)
# ─────────────────────────────────────────────────────────────

def _send_meta_event(
    event_name: str,
    is_custom: bool = False,
    value: float = 0.0,
    currency: str = "BRL",
    email: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    fbc: str | None = None,
    fbp: str | None = None,
    external_id: str | None = None,
    event_source_url: str | None = None,
) -> dict | None:
    pixel_id = os.environ.get("META_PIXEL_ID")
    token    = os.environ.get("META_ACCESS_TOKEN")
    if not pixel_id or not token:
        return None

    user_data: dict = {}
    if email:
        user_data["em"] = [_sha256(email)]
    if phone:
        user_data["ph"] = [_sha256(_normalize_phone(phone))]
    if name:
        parts = name.strip().split()
        user_data["fn"] = [_sha256(parts[0])]
        if len(parts) > 1:
            user_data["ln"] = [_sha256(" ".join(parts[1:]))]
    if fbc:
        user_data["fbc"] = fbc
    if fbp:
        user_data["fbp"] = fbp
    if external_id:
        user_data["external_id"] = [_sha256(str(external_id))]

    event: dict = {
        "event_name": event_name,
        "event_time": int(time.time()),
        "action_source": "system_generated",
        "user_data": user_data,
        "custom_data": {"value": value, "currency": currency,
                        "lead_event_source": "Pipedrive", "event_source": "crm"},
    }
    if is_custom:
        event["data_processing_options"] = []
    if event_source_url:
        event["event_source_url"] = event_source_url

    payload = {"data": [event], "access_token": token}
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{pixel_id}/events",
            json=payload, timeout=10,
        )
        return {"ok": r.status_code < 300, "status": r.status_code, "body": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# GA4 MEASUREMENT PROTOCOL
# ─────────────────────────────────────────────────────────────

def _send_ga4_event(
    event_name: str,
    value: float = 0.0,
    currency: str = "BRL",
    client_id: str | None = None,
    deal_id: str | None = None,
) -> dict | None:
    measurement_id = os.environ.get("GA4_MEASUREMENT_ID")
    api_secret     = os.environ.get("GA4_API_SECRET")
    if not measurement_id or not api_secret:
        return None

    params: dict = {"value": value, "currency": currency}
    if deal_id:
        params["deal_id"] = deal_id
        params["transaction_id"] = f"pd_{deal_id}"

    payload = {
        "client_id": client_id or f"pd.{deal_id or int(time.time())}",
        "events": [{"name": event_name, "params": params}],
    }
    if deal_id:
        payload["user_id"] = str(deal_id)

    try:
        r = requests.post(
            "https://www.google-analytics.com/mp/collect",
            params={"measurement_id": measurement_id, "api_secret": api_secret},
            json=payload, timeout=10,
        )
        return {"ok": r.status_code in (200, 204), "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# GOOGLE ADS OFFLINE CONVERSIONS
# ─────────────────────────────────────────────────────────────

def _send_gads_conversion(
    conv_action_env: str,
    value: float = 0.0,
    currency: str = "BRL",
    gclid: str | None = None,
    email: str | None = None,
) -> dict | None:
    customer_id  = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
    dev_token    = os.environ.get("GOOGLE_ADS_DEV_TOKEN")
    client_id    = os.environ.get("GOOGLE_ADS_CLIENT_ID")
    client_secret= os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
    refresh_token= os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
    login_cid    = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    action_id    = os.environ.get(conv_action_env)

    if not all([customer_id, dev_token, client_id, client_secret, refresh_token, action_id]):
        print(f"⚠️ [GAds] credenciais incompletas para {conv_action_env}")
        return None

    if not gclid and not email:
        print(f"⚠️ [GAds] sem gclid nem email — conversão ignorada ({conv_action_env})")
        return None

    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException

        config = {
            "developer_token": dev_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "use_proto_plus": True,
        }
        if login_cid:
            config["login_customer_id"] = login_cid
        client = GoogleAdsClient.load_from_dict(config)

        svc = client.get_service("ConversionUploadService")
        conv_resource = (
            f"customers/{customer_id}/conversionActions/{action_id}"
        )

        click_conv = client.get_type("ClickConversion")
        click_conv.conversion_action = conv_resource
        click_conv.conversion_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S+00:00")
        click_conv.currency_code = currency
        if value:
            click_conv.conversion_value = value
        if gclid:
            click_conv.gclid = gclid
        if email:
            uie = client.get_type("UserIdentifier")
            uie.hashed_email = _sha256(email.lower().strip())
            click_conv.user_identifiers.append(uie)

        req = client.get_type("UploadClickConversionsRequest")
        req.customer_id = customer_id
        req.conversions.append(click_conv)
        req.partial_failure = True

        response = svc.upload_click_conversions(request=req)
        if response.partial_failure_error.code:
            msg = response.partial_failure_error.message
            print(f"⚠️ [GAds] partial_failure: {msg}")
            return {"ok": False, "error": msg, "action_id": action_id}

        print(f"✅ [GAds] conversão enviada action={action_id} value={value}")
        return {"ok": True, "action_id": action_id, "value": value}

    except Exception as exc:
        print(f"❌ [GAds] erro: {exc}")
        return {"ok": False, "error": str(exc), "action_id": action_id}


# ─────────────────────────────────────────────────────────────
# DISPATCHER PRINCIPAL
# ─────────────────────────────────────────────────────────────

def fire_funnel_event(
    trigger: str,
    deal: dict,
    person: dict | None = None,
    value: float = 0.0,
) -> dict:
    """Dispara eventos de funil para todos os canais configurados.

    Args:
        trigger: "stage_{id}" ou "status_won" ou "status_lost"
        deal:    objeto deal completo do Pipedrive
        person:  objeto person completo (opcional, para hashing PII)
        value:   valor de conversão em BRL (usado em WON)

    Returns:
        dict com resultado de cada canal
    """
    # Resolve config de eventos para este trigger
    if trigger.startswith("stage_"):
        stage_id = int(trigger.split("_")[1])
        cfg = STAGE_EVENT_MAP.get(stage_id)
        if not cfg:
            return {"skipped": True, "reason": f"no_event_for_stage_{stage_id}"}
    elif trigger == "status_won":
        cfg = WON_EVENTS
    elif trigger == "status_lost":
        cfg = LOST_EVENTS
    else:
        return {"skipped": True, "reason": f"unknown_trigger:{trigger}"}

    # Extrai dados do person para hashing
    pdata   = _extract_person_data(person)
    email   = pdata.get("email") or None
    phone   = pdata.get("phone") or None
    name    = pdata.get("name") or None
    deal_id = str(deal.get("id") or "")
    gclid   = deal.get("gclid") or None

    results: dict = {}

    # ── Meta CAPI ──────────────────────────────────────────
    meta_cfg = cfg.get("meta")
    if meta_cfg:
        meta_event, is_custom = (meta_cfg if isinstance(meta_cfg, tuple) else (meta_cfg, False))
        results["meta"] = _send_meta_event(
            event_name=meta_event, is_custom=is_custom,
            value=value, email=email, phone=phone, name=name,
            external_id=deal_id,
        )

    # ── GA4 Measurement Protocol ───────────────────────────
    ga4_event = cfg.get("ga4")
    if ga4_event:
        results["ga4"] = _send_ga4_event(
            event_name=ga4_event, value=value, deal_id=deal_id,
        )

    # ── Google Ads Offline ─────────────────────────────────
    gads_env = cfg.get("gads")
    if gads_env:
        results["gads"] = _send_gads_conversion(
            conv_action_env=gads_env, value=value, gclid=gclid, email=email,
        )

    print(f"🎯 [conversions] trigger={trigger} deal={deal_id} → {json.dumps(results, ensure_ascii=False)}")
    return results


# ─────────────────────────────────────────────────────────────
# HELPERS DE DETECÇÃO DE MUDANÇA (usado em main.py)
# ─────────────────────────────────────────────────────────────

def detect_triggers(payload: dict) -> list[str]:
    """A partir do payload do webhook Pipedrive, retorna lista de triggers a disparar.

    Detecta:
    - Criação de deal (added.deal / create.deal) → "stage_{current_stage}" da stage inicial
    - Mudança de stage_id → "stage_{new_id}"
    - Mudança de status para won  → "status_won"
    - Mudança de status para lost → "status_lost"

    Suporta tanto v1.0 (previous = snapshot completo) quanto v2.0 (previous = delta/null em create).
    """
    current  = payload.get("current") or {}
    previous = payload.get("previous") or {}
    meta     = payload.get("meta") or {}
    is_v2    = str(meta.get("version", "")).startswith("2")
    action   = (
        meta.get("action")
        or payload.get("event_action")
        or (payload.get("event") or "").split(".")[0]
        or ""
    ).lower()
    is_create = action in ("create", "added") or (is_v2 and not previous)
    triggers = []

    curr_stage  = current.get("stage_id")
    prev_stage  = previous.get("stage_id")

    if is_create and curr_stage:
        # Deal recém-criado: dispara o evento da stage de entrada (geralmente "Lead")
        triggers.append(f"stage_{curr_stage}")
    else:
        stage_changed = (
            ("stage_id" in previous) if is_v2
            else (curr_stage and curr_stage != prev_stage)
        )
        if curr_stage and stage_changed:
            triggers.append(f"stage_{curr_stage}")

    curr_status = current.get("status")
    prev_status = previous.get("status")
    if is_create:
        # Em create, status já vem populado mas previous é vazio → só dispara se won/lost
        # (não disparar Purchase só porque o deal nasceu open, óbvio)
        if curr_status in ("won", "lost"):
            triggers.append(f"status_{curr_status}")
    else:
        status_changed = (
            ("status" in previous) if is_v2
            else (curr_status != prev_status)
        )
        if status_changed:
            if curr_status == "won":
                triggers.append("status_won")
            elif curr_status == "lost":
                triggers.append("status_lost")

    return triggers


