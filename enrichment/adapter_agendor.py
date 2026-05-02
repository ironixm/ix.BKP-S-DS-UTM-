"""Adapter Agendor — mapeia campos enriquecidos para a estrutura de PUT.

Custom field IDs Agendor (BKP):
    Org:    28645=Faturamento Médio Mensal, 28646=Nome Contato Principal,
            28644=Número de Funcionários
    Person: 19677=Faturamento, 19678=Nº Funcionários, 19679=Segmento,
            19686=FBCLID, 19685=GCLID, 19687=Página de Conversão,
            19682=UTM Campaign, 19683=UTM Content, 19681=UTM Medium,
            19680=UTM Source, 19684=UTM Term, 19688=Wix Contact ID
"""
from typing import Optional

from agendor_api import (  # type: ignore
    get_organization, update_organization,
    get_person, update_person,
    _request,
)


CRM_NAME = "agendor"

ORG_CUSTOM_FIELDS = {
    "faturamento_mensal": 28645,
    "nome_contato_principal": 28646,
    "num_funcionarios": 28644,
}

PERSON_CUSTOM_FIELDS = {
    "faturamento": 19677,
    "num_funcionarios": 19678,
    "segmento": 19679,
    "fbclid": 19686,
    "gclid": 19685,
    "pagina_conversao": 19687,
    "utm_campaign": 19682,
    "utm_content": 19683,
    "utm_medium": 19681,
    "utm_source": 19680,
    "utm_term": 19684,
    "wix_contact_id": 19688,
}


def get_org(org_id) -> Optional[dict]:
    """Retorna org Agendor com keys flat (acessamos `_raw_agendor` se existir).

    `_normalize_org` em agendor_api.py reduz o objeto a {id, name, _raw_agendor}.
    Aqui devolvemos um dict que combina o normalizado com o raw, para que
    `org.get('website')`, `org.get('cnpj')`, `org.get('legalName')` etc funcionem.
    """
    o = get_organization(org_id)
    if not o:
        return None
    raw = o.get("_raw_agendor") or {}
    merged = dict(raw)
    merged.update({k: v for k, v in o.items() if k != "_raw_agendor" and v not in (None, "")})
    merged["_raw_agendor"] = raw
    return merged


def org_needs_enrichment(org: dict) -> bool:
    """Decide se vale a pena enriquecer (algum campo essencial vazio)."""
    if not org:
        return False
    return not (org.get("legalName")
                and (org.get("address") or {}).get("city")
                and org.get("sector"))


def org_cnpj(org: dict) -> Optional[str]:
    if not org:
        return None
    return org.get("cnpj") or (org.get("_raw_agendor") or {}).get("cnpj")


def update_org_with_enrichment(org_id, enriched: dict) -> dict:
    """Aplica payload normalizado (vindo do enrichment.cnpj) ao Agendor.

    Só preenche campos vazios (não sobrescreve dados manuais do vendedor).
    """
    current = get_org(org_id) or {}
    payload = {}

    # Campos nativos
    if enriched.get("razao_social") and not current.get("legalName"):
        payload["legalName"] = enriched["razao_social"]
    if enriched.get("nome_fantasia") and not current.get("name"):
        payload["name"] = enriched["nome_fantasia"]
    if enriched.get("cnpj") and not current.get("cnpj"):
        payload["cnpj"] = enriched["cnpj"]
    if enriched.get("email") and not current.get("contact", {}).get("email"):
        payload.setdefault("contact", {})["email"] = enriched["email"]
    if enriched.get("telefone") and not current.get("contact", {}).get("workPhone"):
        payload.setdefault("contact", {})["workPhone"] = enriched["telefone"]

    # Endereço
    addr = current.get("address") or {}
    new_addr = {}
    for src, dst in [("logradouro", "street"), ("numero", "streetNumber"),
                     ("complemento", "complement"), ("bairro", "district"),
                     ("municipio", "city"), ("uf", "state"), ("cep", "postalCode")]:
        if enriched.get(src) and not addr.get(dst):
            new_addr[dst] = enriched[src]
    if new_addr:
        payload["address"] = {**addr, **new_addr}

    # Setor (mapeia CNAE → sector text)
    if enriched.get("cnae_descricao") and not current.get("sector"):
        # Agendor sector aceita ID; pra MVP gravamos description em
        # "details" como texto livre.
        details = current.get("description") or ""
        if enriched["cnae_descricao"] not in details:
            payload["description"] = (details + "\n[ix.enrich] CNAE: "
                                      + enriched["cnae_descricao"]).strip()

    # Custom fields (faturamento estimado a partir do capital_social/porte)
    custom = []
    if enriched.get("porte") and not _has_custom(current, ORG_CUSTOM_FIELDS["num_funcionarios"]):
        # Estimativa de funcionários por porte (heurística)
        porte_to_count = {
            "MEI": 1, "MICRO EMPRESA": 5, "EMPRESA DE PEQUENO PORTE": 30,
            "DEMAIS": 100,
        }
        n = porte_to_count.get((enriched["porte"] or "").upper())
        if n:
            custom.append({"customField": ORG_CUSTOM_FIELDS["num_funcionarios"],
                           "value": n})
    if custom:
        payload["customFields"] = custom

    if not payload:
        return {"ok": True, "skipped": "no_changes", "org_id": org_id}

    res = update_organization(org_id, payload)
    return {"ok": True, "applied": list(payload.keys()),
            "org_id": org_id, "raw": res}


def _has_custom(entity: dict, field_id: int) -> bool:
    for cf in (entity.get("customFields") or []):
        if cf.get("customField") == field_id and cf.get("value"):
            return True
    return False


# ─── Person ─────────────────────────────────────────────────
def get_person_data(person_id) -> Optional[dict]:
    return get_person(person_id)


def update_person_with_enrichment(person_id, enriched: dict) -> dict:
    current = get_person_data(person_id) or {}
    payload = {}
    contact = current.get("contact") or {}

    if enriched.get("linkedin_url") and not contact.get("linkedin"):
        payload.setdefault("contact", {})["linkedin"] = enriched["linkedin_url"]
    if enriched.get("whatsapp_business") and not contact.get("whatsapp"):
        wa = enriched["whatsapp_business"]
        if isinstance(wa, dict) and wa.get("profile_url"):
            payload.setdefault("contact", {})["whatsapp"] = wa["profile_url"]

    if not payload:
        return {"ok": True, "skipped": "no_changes", "person_id": person_id}

    res = update_person(person_id, payload)
    return {"ok": True, "applied": list(payload.keys()),
            "person_id": person_id, "raw": res}
