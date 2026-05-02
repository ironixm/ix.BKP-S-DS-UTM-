"""Google Programmable Search (CSE) — fallback para LinkedIn/CNPJ por nome.

ENV:
    GOOGLE_CSE_API_KEY
    GOOGLE_CSE_CX (default: b799e5585cbd040d4 — CX original BKP)
"""
import os
from typing import Optional

import requests


_DEFAULT_CX = "b799e5585cbd040d4"
_TIMEOUT = 10


def _key() -> Optional[str]:
    return os.getenv("GOOGLE_CSE_API_KEY") or os.getenv("GOOGLE_CSE_KEY")


def search(query: str, *, num: int = 5, site: str = None) -> list:
    """Retorna lista de items {title, link, snippet}. [] se desabilitado."""
    key = _key()
    if not key or not query:
        return []
    cx = os.getenv("GOOGLE_CSE_CX") or _DEFAULT_CX
    q = f"site:{site} {query}" if site else query
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": key, "cx": cx, "q": q, "num": min(num, 10)},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return [
                {"title": it.get("title"),
                 "link": it.get("link"),
                 "snippet": it.get("snippet")}
                for it in (r.json().get("items") or [])
            ]
    except Exception as e:
        print(f"[enrichment.google_cse] erro: {e}", flush=True)
    return []


def find_linkedin_company(company_name: str) -> Optional[str]:
    if not company_name:
        return None
    items = search(company_name, num=3, site="linkedin.com/company")
    for it in items:
        link = (it.get("link") or "").rstrip("/")
        if "linkedin.com/company/" in link:
            return link
    return None


def find_linkedin_person(name: str, company: str = None) -> Optional[str]:
    q = name + (" " + company if company else "")
    items = search(q, num=3, site="linkedin.com/in")
    for it in items:
        link = (it.get("link") or "").rstrip("/")
        if "linkedin.com/in/" in link:
            return link
    return None
