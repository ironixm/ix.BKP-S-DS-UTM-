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

from mappings import (
    DEAL_FONTE_KEY, DEAL_CANAL_KEY, DEAL_CAMPANHA_KEY,
    DEAL_CONTEUDO_KEY, DEAL_ANUNCIO_ISOLADO,
)


# ─────────────────────────────────────────────────────────────
# MAPEAMENTO DE ESTÁGIOS → EVENTOS
# ─────────────────────────────────────────────────────────────

# Cada entrada: stage_id → {meta, ga4, gads}
# meta: None = não dispara | str = nome do evento | (str, True) = evento custom
# gads: None = não dispara | str = env var com o Conversion Action ID
#
# ⚠️ Stage IDs do Agendor BKP (Funil "Funil de Vendas" id=713891).
# Documentação: docs/agendor-bkp-eventos.md
STAGE_EVENT_MAP: dict[int, dict] = {
    3735676: {"meta": "Lead",                  "ga4": "generate_lead", "gads": None},                              # Leads
    2914195: {"meta": "CompleteRegistration",  "ga4": "qualify_lead",  "gads": "GADS_CONV_DEMO_AGENDADA"},         # Contato 1 (MQL)
    2914196: {"meta": "SubmitApplication",     "ga4": "working_lead",  "gads": "GADS_CONV_NEGOCIACAO_INICIADA"},   # Contato 2 (SQL)
    2914197: {"meta": "Schedule",              "ga4": "schedule",      "gads": "GADS_CONV_DEMO_AGENDADA"},         # Apresentação (OPTY)
    2914198: {"meta": ("Proposal", True),      "ga4": "view_proposal", "gads": "GADS_CONV_NEGOCIACAO_INICIADA"},   # Fechamento (Negociação)
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


_BR_UF = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
          "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}


def _normalize_state(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    if len(s) == 2 and s.upper() in _BR_UF:
        return s.lower()
    return s.lower()


def _normalize_zip(z: str | None) -> str | None:
    if not z:
        return None
    return "".join(c for c in z if c.isdigit())[:8] or None


def _extract_geo_from_deal(deal: dict | None) -> dict:
    """Extrai city/state/zip/country da org vinculada (Agendor/Pipedrive)."""
    out: dict = {"country": "br"}
    if not deal:
        return out
    org = deal.get("organization") or deal.get("org_id") or deal.get("org")
    if isinstance(org, int):
        try:
            from agendor_api import get_organization  # type: ignore
            o = get_organization(org)
            org = (o or {}).get("_raw_agendor") or o
        except Exception:
            org = None
    if not isinstance(org, dict):
        return out
    raw = org.get("_raw_agendor") or org
    addr = raw.get("address") if isinstance(raw.get("address"), dict) else None
    if addr:
        out["city"] = addr.get("city") or addr.get("municipio")
        out["state"] = addr.get("state") or addr.get("uf")
        out["zip"] = addr.get("postalCode") or addr.get("cep")
    return {k: v for k, v in out.items() if v}


def _extract_person_data(person: dict | None) -> dict:
    """Extrai email, phone, nome — funciona com Pipedrive e Agendor."""
    if not person:
        return {}
    result = {"name": person.get("name") or ""}

    # ── Agendor: contact.email (str), contact.mobile/whatsapp/work (str) ──
    contact = person.get("contact")
    if isinstance(contact, dict):
        result["email"] = contact.get("email") or ""
        result["phone"] = (
            contact.get("whatsapp") or contact.get("mobile") or contact.get("work") or ""
        )
        return result

    # ── Pipedrive: email/phone são arrays de {value, ...} ──
    emails = person.get("email") or []
    if emails:
        e = emails[0]
        result["email"] = (e.get("value") if isinstance(e, dict) else e) or ""
    elif isinstance(person.get("email"), str):
        result["email"] = person.get("email")

    phones = person.get("phone") or []
    if phones:
        p = phones[0]
        result["phone"] = (p.get("value") if isinstance(p, dict) else p) or ""
    elif isinstance(person.get("phone"), str):
        result["phone"] = person.get("phone")

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
    fbclid: str | None = None,
    external_id: str | None = None,
    event_source_url: str | None = None,
    event_id: str | None = None,
    client_ip: str | None = None,
    client_user_agent: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = "br",
    date_of_birth: str | None = None,
    gender: str | None = None,
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
    if city:
        user_data["ct"] = [_sha256("".join(c for c in city.lower() if c.isalnum()))]
    st = _normalize_state(state)
    if st:
        user_data["st"] = [_sha256(st)]
    zp = _normalize_zip(zip_code)
    if zp:
        user_data["zp"] = [_sha256(zp)]
    if country:
        user_data["country"] = [_sha256(country.lower()[:2])]
    if date_of_birth:
        user_data["db"] = [_sha256("".join(c for c in date_of_birth if c.isdigit()))]
    if gender:
        user_data["ge"] = [_sha256(gender.strip().lower()[:1])]
    if fbc:
        user_data["fbc"] = fbc
    elif fbclid:
        user_data["fbc"] = f"fb.1.{int(time.time()*1000)}.{fbclid}"
    if fbp:
        user_data["fbp"] = fbp
    if external_id:
        user_data["external_id"] = [_sha256(str(external_id))]
    if client_ip:
        user_data["client_ip_address"] = client_ip
    if client_user_agent:
        user_data["client_user_agent"] = client_user_agent

    if not event_id and external_id:
        event_id = f"{event_name}.{external_id}"

    event: dict = {
        "event_name": event_name,
        "event_time": int(time.time()),
        "action_source": "system_generated",
        "user_data": user_data,
        "custom_data": {"value": value, "currency": currency,
                        "lead_event_source": "Agendor", "event_source": "crm"},
    }
    if event_id:
        event["event_id"] = event_id
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
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_content: str | None = None,
    utm_term: str | None = None,
    gclid: str | None = None,
    ga_session_id: str | None = None,
) -> dict | None:
    measurement_id = os.environ.get("GA4_MEASUREMENT_ID")
    api_secret     = os.environ.get("GA4_API_SECRET")
    if not measurement_id or not api_secret:
        return None

    params: dict = {"value": value, "currency": currency}
    if deal_id:
        params["deal_id"] = deal_id
        params["transaction_id"] = f"pd_{deal_id}"

    if utm_source:   params["campaign_source"]  = utm_source
    if utm_medium:   params["campaign_medium"]  = utm_medium
    if utm_campaign: params["campaign_name"]    = utm_campaign
    if utm_content:  params["campaign_content"] = utm_content
    if utm_term:     params["campaign_term"]    = utm_term
    if gclid:        params["gclid"]            = gclid
    if ga_session_id:
        params["session_id"] = ga_session_id
    elif deal_id:
        params["session_id"] = f"pd_{deal_id}"

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
        missing = [k for k,v in {
            "GOOGLE_ADS_CUSTOMER_ID": customer_id, "GOOGLE_ADS_DEV_TOKEN": dev_token,
            "GOOGLE_ADS_CLIENT_ID": client_id, "GOOGLE_ADS_CLIENT_SECRET": client_secret,
            "GOOGLE_ADS_REFRESH_TOKEN": refresh_token, conv_action_env: action_id,
        }.items() if not v]
        print(f"⚠️ [GAds] credenciais incompletas para {conv_action_env} — faltando: {missing}")
        return {"ok": False, "status": "skipped", "reason": "missing_credentials",
                "missing": missing, "action_id": action_id}

    if not gclid and not email:
        print(f"⚠️ [GAds] sem gclid nem email — conversão ignorada ({conv_action_env})")
        return {"ok": False, "status": "skipped", "reason": "no_gclid_or_email",
                "action_id": action_id}

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
    fbclid  = deal.get("fbclid") or None
    fbc     = deal.get("fbc") or None
    fbp     = deal.get("fbp") or None
    client_ip = deal.get("client_ip") or deal.get("_client_ip")
    client_ua = deal.get("client_user_agent") or deal.get("_client_user_agent")
    geo = _extract_geo_from_deal(deal)

    # Extrai UTMs dos custom fields do Agendor/Pipedrive
    utm_source   = deal.get(DEAL_FONTE_KEY) or deal.get("utm_source") or None
    utm_medium   = deal.get(DEAL_CANAL_KEY) or deal.get("utm_medium") or None
    utm_campaign = deal.get(DEAL_CAMPANHA_KEY) or deal.get("utm_campaign") or None
    utm_content  = deal.get(DEAL_CONTEUDO_KEY) or deal.get(DEAL_ANUNCIO_ISOLADO) or deal.get("utm_content") or None
    ga_client_id = deal.get("ga_client_id") or deal.get("ga_cid") or None
    ga_session_id = deal.get("ga_session_id") or None

    results: dict = {}

    # ── Meta CAPI ──────────────────────────────────────────
    meta_cfg = cfg.get("meta")
    if meta_cfg:
        meta_event, is_custom = (meta_cfg if isinstance(meta_cfg, tuple) else (meta_cfg, False))
        results["meta"] = _send_meta_event(
            event_name=meta_event, is_custom=is_custom,
            value=value, email=email, phone=phone, name=name,
            external_id=deal_id,
            fbc=fbc, fbp=fbp, fbclid=fbclid,
            client_ip=client_ip, client_user_agent=client_ua,
            city=geo.get("city"), state=geo.get("state"),
            zip_code=geo.get("zip"), country=geo.get("country", "br"),
        )

    # ── GA4 Measurement Protocol ───────────────────────────
    ga4_event = cfg.get("ga4")
    if ga4_event:
        results["ga4"] = _send_ga4_event(
            event_name=ga4_event, value=value, deal_id=deal_id,
            client_id=ga_client_id,
            utm_source=utm_source, utm_medium=utm_medium,
            utm_campaign=utm_campaign, utm_content=utm_content,
            gclid=gclid, ga_session_id=ga_session_id,
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
    """A partir do payload do webhook (Pipedrive ou Agendor), retorna triggers a disparar.

    Suporta:
    - Pipedrive v1.0 (previous = snapshot completo)
    - Pipedrive v2.0 (previous = delta)
    - Agendor (meta.agendor_event indica o tipo via path da URL)
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

    curr_stage  = current.get("stage_id")
    curr_status = current.get("status")

    # ─── AGENDOR: o "event" vem no path → meta.agendor_event ───
    ag_event = (meta.get("agendor_event") or "").lower()
    if ag_event:
        if not ag_event.startswith("on_deal_"):
            return []
        if ag_event == "on_deal_won":
            return ["status_won"]
        if ag_event == "on_deal_lost":
            return ["status_lost"]
        if ag_event in ("on_deal_created", "on_deal_stage_updated"):
            return [f"stage_{curr_stage}"] if curr_stage else []
        return []  # on_deal_updated / on_deal_deleted → sem conversão

    # ─── PIPEDRIVE (legado) ───
    is_create = action in ("create", "added") or (is_v2 and not previous)
    triggers = []
    prev_stage  = previous.get("stage_id")
    prev_status = previous.get("status")

    if is_create and curr_stage:
        triggers.append(f"stage_{curr_stage}")
    else:
        stage_changed = (
            ("stage_id" in previous) if is_v2
            else (curr_stage and curr_stage != prev_stage)
        )
        if curr_stage and stage_changed:
            triggers.append(f"stage_{curr_stage}")

    if is_create:
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


