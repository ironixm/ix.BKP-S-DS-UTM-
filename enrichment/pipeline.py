"""Pipeline orquestrador de enriquecimento.

Função principal: `enrich_organization(org_id, *, mode='auto', adapter=None)`

Modos:
    auto   — só preenche campos vazios (idempotente, default)
    force  — re-busca tudo e sobrescreve
    skip   — só verifica se precisa (não chama APIs externas)
"""
import os
import time
from typing import Optional

from .cnpj import fetch_cnpj, clean_cnpj, is_valid_cnpj
from .scraping import scrape_cnpj_from_domain
from .email_utils import (get_domain, is_commercial_email,
                          is_disposable_email_local)
from .ninjapear import (check_disposable_email, fetch_company_logo,
                        fetch_company_details)
from .whatsapp import check_whatsapp_business
from .google_cse import find_linkedin_company, find_linkedin_person


def _enabled(name: str, default: str = "ON") -> bool:
    val = (os.getenv(name) or default).upper()
    return val in ("ON", "TRUE", "1", "YES")


def _log(event: str, payload: dict):
    """Escreve no events.log para visualização no MadMode."""
    try:
        from logger import log_event  # type: ignore
        log_event(event, payload)
    except Exception as e:
        print(f"[enrichment.log] falha {e}", flush=True)


def enrich_organization(org_id, *, mode: str = "auto", adapter=None) -> dict:
    """Enriquece uma org no CRM. Retorna dict com sources/status/duration_ms.

    Args:
        org_id: ID da org no CRM
        mode: auto|force
        adapter: módulo com get_org/update_org_with_enrichment/org_cnpj
                 (default = adapter_agendor)
    """
    start = time.time()
    if adapter is None:
        from . import adapter_agendor as adapter

    if not _enabled("ENRICHMENT_ENABLED"):
        return {"ok": False, "reason": "disabled", "org_id": org_id}

    org = adapter.get_org(org_id)
    if not org:
        return {"ok": False, "reason": "org_not_found", "org_id": org_id}

    sources_used = []
    enriched_data = {}

    # ── 1. CNPJ ──
    cnpj = adapter.org_cnpj(org)
    if not cnpj or not is_valid_cnpj(cnpj):
        # tenta scraping pelo website da org
        website = (org.get("website") or "").strip()
        if website and _enabled("ENRICHMENT_SITE_SCRAPING_ENABLED"):
            scraped = scrape_cnpj_from_domain(website)
            if scraped:
                cnpj = scraped
                sources_used.append("scraping")
                enriched_data["cnpj"] = scraped

    if cnpj and is_valid_cnpj(cnpj):
        cnpj_data = fetch_cnpj(cnpj)
        if cnpj_data:
            sources_used.append(cnpj_data.get("_source", "cnpj"))
            enriched_data.update(cnpj_data)

    # ── 2. Company details (NinjaPear paid) ──
    website = (org.get("website") or enriched_data.get("website") or "").strip()
    if website and _enabled("ENRICHMENT_COMPANY_DETAILS_ENABLED"):
        cd = fetch_company_details(website)
        if cd.get("ok"):
            sources_used.append("ninjapear_details")
            enriched_data["np_details"] = cd["data"]

    # ── 3. Company logo (NinjaPear free) ──
    if website and _enabled("ENRICHMENT_COMPANY_LOGO_ENABLED"):
        logo = fetch_company_logo(website)
        if logo.get("ok"):
            sources_used.append("ninjapear_logo")
            enriched_data["logo_url"] = (logo["data"] or {}).get("logo_url")

    # ── 4. LinkedIn da empresa via Google CSE ──
    if _enabled("ENRICHMENT_LINKEDIN_ENABLED"):
        company_name = (enriched_data.get("razao_social")
                        or enriched_data.get("nome_fantasia")
                        or org.get("name"))
        if company_name:
            li = find_linkedin_company(company_name)
            if li:
                sources_used.append("google_cse_linkedin")
                enriched_data["linkedin_url"] = li

    # ── 5. Aplicar no CRM ──
    apply = {"skipped": "no_data"}
    if enriched_data:
        try:
            apply = adapter.update_org_with_enrichment(org_id, enriched_data)
        except Exception as e:
            apply = {"ok": False, "error": str(e)}

    duration_ms = int((time.time() - start) * 1000)
    result = {
        "ok": True,
        "entity": "organization",
        "entity_id": org_id,
        "sources": sources_used,
        "fields_collected": list(enriched_data.keys()),
        "apply": apply,
        "duration_ms": duration_ms,
        "mode": mode,
    }
    _log("enrichment_org", result)
    return result


def enrich_person(person_id, *, mode: str = "auto", adapter=None) -> dict:
    start = time.time()
    if adapter is None:
        from . import adapter_agendor as adapter

    if not _enabled("ENRICHMENT_ENABLED"):
        return {"ok": False, "reason": "disabled", "person_id": person_id}

    person = adapter.get_person_data(person_id)
    if not person:
        return {"ok": False, "reason": "person_not_found",
                "person_id": person_id}

    sources_used = []
    enriched_data = {}
    contact = person.get("contact") or {}

    # ── 1. Email checks ──
    email = contact.get("email") if isinstance(contact, dict) else None
    if isinstance(email, list):
        email = (email[0] or {}).get("email") if email else None
    if email:
        enriched_data["is_commercial_email"] = is_commercial_email(email)
        enriched_data["is_disposable_email"] = is_disposable_email_local(email)
        if _enabled("ENRICHMENT_DISPOSABLE_EMAIL_ENABLED"):
            disp = check_disposable_email(email)
            if disp.get("ok"):
                sources_used.append("ninjapear_disposable")
                enriched_data["np_email_check"] = disp["data"]

    # ── 2. WhatsApp Business ──
    phone = (contact.get("whatsapp") if isinstance(contact, dict) else None) \
        or (contact.get("mobile") if isinstance(contact, dict) else None)
    if phone and _enabled("ENRICHMENT_WHATSAPP_ENABLED"):
        wa = check_whatsapp_business(phone)
        if wa.get("ok"):
            sources_used.append("whatsapp_check")
            enriched_data["whatsapp_business"] = wa.get("data")

    # ── 3. LinkedIn da pessoa via Google CSE ──
    if _enabled("ENRICHMENT_LINKEDIN_ENABLED"):
        name = person.get("name") or ""
        org_ref = person.get("organization") or {}
        company = org_ref.get("name") if isinstance(org_ref, dict) else None
        if name:
            li = find_linkedin_person(name, company)
            if li:
                sources_used.append("google_cse_linkedin")
                enriched_data["linkedin_url"] = li

    # ── 4. Aplicar ──
    apply = {"skipped": "no_data"}
    if enriched_data:
        try:
            apply = adapter.update_person_with_enrichment(person_id, enriched_data)
        except Exception as e:
            apply = {"ok": False, "error": str(e)}

    duration_ms = int((time.time() - start) * 1000)
    result = {
        "ok": True,
        "entity": "person",
        "entity_id": person_id,
        "sources": sources_used,
        "fields_collected": list(enriched_data.keys()),
        "apply": apply,
        "duration_ms": duration_ms,
        "mode": mode,
    }
    _log("enrichment_person", result)
    return result
