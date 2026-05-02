"""Mapper genérico: converte payloads de form (Meta + GAds) → estrutura Agendor.

Saída padrão:
{
  "external_id":     "<provider>:<form>:<lead_id>",
  "name":            "...",
  "email":           "...",
  "phone":           "...",
  "company":         "...",
  "city":            "...",
  "state":           "...",
  "raw_fields":      {...},
  "source_meta": {
    "form_id":      "...",
    "form_name":    "...",
    "ad_id":        "...",
    "campaign_id":  "...",
    "platform":     "..."
  }
}
"""
from __future__ import annotations
import re

# Heurística PT-BR + EN para identificar campos comuns
_RX = {
    "email":   re.compile(r"e[-_ ]?mail|^email", re.I),
    "phone":   re.compile(r"phone|telefone|whats|celular|mobile|tel\b", re.I),
    "name":    re.compile(r"^(full[_ ]?)?name$|nome[_ ]?completo|^nome$", re.I),
    "first":   re.compile(r"first[_ ]?name|primeiro[_ ]?nome", re.I),
    "last":    re.compile(r"last[_ ]?name|sobrenome|último[_ ]?nome", re.I),
    "company": re.compile(r"company|empresa|razao[_ ]?social|cnpj", re.I),
    "city":    re.compile(r"^city$|cidade", re.I),
    "state":   re.compile(r"^state$|estado|^uf$", re.I),
    "zip":     re.compile(r"zip|cep|postal", re.I),
    "job":     re.compile(r"job[_ ]?title|cargo|posicao|posição", re.I),
    "size":    re.compile(r"company[_ ]?size|tamanho|funcionarios|funcionários", re.I),
    "revenue": re.compile(r"revenue|faturamento", re.I),
}


def _classify(field_name: str) -> str | None:
    if not field_name:
        return None
    for key, rx in _RX.items():
        if rx.search(field_name):
            return key
    return None


def _flatten_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x)
    return str(v).strip()


def from_meta_lead(lead: dict) -> dict:
    """Converte field_data do Meta Lead Ads."""
    fd = lead.get("field_data") or []
    raw: dict = {}
    classified: dict = {}
    for f in fd:
        name = (f.get("name") or "").strip()
        val  = _flatten_value(f.get("values"))
        if not name:
            continue
        raw[name] = val
        k = _classify(name)
        if k and val and not classified.get(k):
            classified[k] = val

    # Compor full name se só tiver first/last
    if not classified.get("name"):
        fn = classified.get("first", "")
        ln = classified.get("last", "")
        composed = f"{fn} {ln}".strip()
        if composed:
            classified["name"] = composed

    lead_id = str(lead.get("id") or "")
    form_id = str(lead.get("form_id") or "")
    return {
        "external_id": f"meta:{form_id}:{lead_id}",
        "lead_id": lead_id,
        "name":    classified.get("name"),
        "email":   classified.get("email"),
        "phone":   classified.get("phone"),
        "company": classified.get("company"),
        "city":    classified.get("city"),
        "state":   classified.get("state"),
        "zip":     classified.get("zip"),
        "job":     classified.get("job"),
        "raw_fields": raw,
        "created_time": lead.get("created_time"),
        "source_meta": {
            "form_id":     form_id,
            "ad_id":       lead.get("ad_id"),
            "ad_name":     lead.get("ad_name"),
            "campaign_id": lead.get("campaign_id"),
            "campaign_name": lead.get("campaign_name"),
            "platform":    lead.get("platform"),
            "is_organic":  lead.get("is_organic"),
        },
    }


def from_gads_lead(payload: dict) -> dict:
    """Converte payload do Google Ads Lead Form Extension webhook.

    Formato típico:
    {
      "lead_id": "...",
      "user_column_data": [
        {"column_name":"FULL_NAME","string_value":"..."},
        {"column_name":"EMAIL","string_value":"..."},
        {"column_name":"PHONE_NUMBER","string_value":"..."},
        ...
      ],
      "campaign_id":"...","gcl_id":"...","form_id":"...","apiVersion":"1.0"
    }
    """
    cols = payload.get("user_column_data") or []
    raw: dict = {}
    classified: dict = {}
    GADS_MAP = {
        "FULL_NAME": "name", "FIRST_NAME": "first", "LAST_NAME": "last",
        "EMAIL": "email", "PHONE_NUMBER": "phone", "WORK_EMAIL": "email",
        "WORK_PHONE": "phone", "COMPANY_NAME": "company", "JOB_TITLE": "job",
        "CITY": "city", "REGION": "state", "POSTAL_CODE": "zip",
        "COUNTRY": "country", "USER_ADDRESS": "address",
    }
    for c in cols:
        name = (c.get("column_name") or "").strip()
        val  = _flatten_value(c.get("string_value") or c.get("value"))
        if not name:
            continue
        raw[name] = val
        k = GADS_MAP.get(name) or _classify(name)
        if k and val and not classified.get(k):
            classified[k] = val

    if not classified.get("name"):
        fn = classified.get("first", "")
        ln = classified.get("last", "")
        composed = f"{fn} {ln}".strip()
        if composed:
            classified["name"] = composed

    lead_id = str(payload.get("lead_id") or "")
    form_id = str(payload.get("form_id") or payload.get("campaign_id") or "")
    return {
        "external_id": f"gads:{form_id}:{lead_id}",
        "lead_id": lead_id,
        "name":    classified.get("name"),
        "email":   classified.get("email"),
        "phone":   classified.get("phone"),
        "company": classified.get("company"),
        "city":    classified.get("city"),
        "state":   classified.get("state"),
        "zip":     classified.get("zip"),
        "job":     classified.get("job"),
        "raw_fields": raw,
        "created_time": payload.get("lead_creation_time") or payload.get("createTime"),
        "source_meta": {
            "form_id":     form_id,
            "campaign_id": payload.get("campaign_id"),
            "gcl_id":      payload.get("gcl_id"),
            "platform":    "google_ads",
        },
    }
