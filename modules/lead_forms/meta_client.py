"""Cliente Meta Lead Ads (Graph API).

Requer token com escopos:
- pages_show_list           (listar páginas)
- pages_read_engagement     (ler dados da página)
- leads_retrieval           (puxar leads dos formulários)
- ads_management            (opcional, para listar formulários)

Token pode ser:
- META_LEADS_TOKEN          (preferido — Page Access Token)
- META_ACCESS_TOKEN         (fallback — pode não ter scopes corretos)
"""
from __future__ import annotations
import os
import json
from urllib import request as urlreq, parse, error as urlerr
from typing import Any

GRAPH = "https://graph.facebook.com/v21.0"


def _token() -> str | None:
    t = (os.environ.get("META_LEADS_TOKEN")
         or os.environ.get("META_PAGE_ACCESS_TOKEN")
         or os.environ.get("META_ACCESS_TOKEN") or "").strip()
    return t or None


def _api(path: str, params: dict | None = None) -> dict:
    tok = _token()
    if not tok:
        return {"ok": False, "error": "META_LEADS_TOKEN/META_ACCESS_TOKEN não configurado"}
    qs = dict(params or {})
    qs["access_token"] = tok
    url = f"{GRAPH}{path}?{parse.urlencode(qs)}"
    req = urlreq.Request(url, method="GET")
    try:
        with urlreq.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
            return {"ok": True, "data": data}
    except urlerr.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {"error": str(e)}
        return {"ok": False, "status": e.code, "error": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_pages() -> dict:
    """Lista páginas acessíveis pelo token."""
    return _api("/me/accounts", {"fields": "id,name,access_token,tasks", "limit": 100})


def get_page_id() -> str | None:
    """Resolve Page ID. Prioridade: env META_PAGE_ID > primeira página retornada."""
    pid = (os.environ.get("META_PAGE_ID") or "").strip()
    if pid:
        return pid
    r = list_pages()
    if r.get("ok"):
        items = (r.get("data") or {}).get("data") or []
        if items:
            return items[0].get("id")
    return None


def list_lead_forms(page_id: str | None = None) -> dict:
    """Lista todos os formulários de lead da página."""
    pid = page_id or get_page_id()
    if not pid:
        return {"ok": False, "error": "page_id não resolvido (configure META_PAGE_ID)"}
    return _api(f"/{pid}/leadgen_forms",
                {"fields": "id,name,status,locale,created_time,leads_count", "limit": 100})


def list_leads(form_id: str, since_unix: int | None = None,
               after: str | None = None, limit: int = 100) -> dict:
    """Lista leads de um formulário (paginado).

    Args:
        form_id: ID do leadgen form
        since_unix: filter por created_time >= since_unix
        after: cursor de paginação
        limit: page size
    """
    params: dict = {
        "fields": "id,created_time,ad_id,ad_name,adset_id,adset_name,campaign_id,"
                  "campaign_name,form_id,is_organic,platform,field_data,"
                  "custom_disclaimer_responses",
        "limit": limit,
    }
    if since_unix:
        params["filtering"] = json.dumps([{
            "field": "time_created", "operator": "GREATER_THAN", "value": since_unix
        }])
    if after:
        params["after"] = after
    return _api(f"/{form_id}/leads", params)


def get_lead(lead_id: str) -> dict:
    """Busca dados de 1 lead específico (usado pelo webhook)."""
    return _api(f"/{lead_id}",
                {"fields": "id,created_time,ad_id,ad_name,adset_id,adset_name,"
                           "campaign_id,campaign_name,form_id,is_organic,platform,"
                           "field_data,custom_disclaimer_responses"})


def iter_all_leads(form_id: str, since_unix: int | None = None, max_pages: int = 50):
    """Iterator que pagina automaticamente."""
    after = None
    for _ in range(max_pages):
        r = list_leads(form_id, since_unix=since_unix, after=after)
        if not r.get("ok"):
            yield {"_error": r}
            return
        d = r.get("data") or {}
        for lead in (d.get("data") or []):
            yield lead
        paging = (d.get("paging") or {}).get("cursors") or {}
        next_url = (d.get("paging") or {}).get("next")
        after = paging.get("after") if next_url else None
        if not after:
            return
