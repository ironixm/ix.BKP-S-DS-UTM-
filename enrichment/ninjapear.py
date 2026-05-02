"""NinjaPear (wrapper Nubela/Proxycurl) — enrichment de empresa/pessoa.

ENV:
    NINJAPEAR_API_KEY — chave (Bearer)

Endpoints free (0 créditos):
    - /contact/disposable-email
    - /company/logo

Endpoints paid:
    - /company/details (2 créditos)
    - /linkedin/company (... créditos)
    - /linkedin/person  (1 crédito)

Se a API key não estiver configurada, todas as funções retornam
{"ok": False, "reason": "missing_api_key"} sem chamar rede.
"""
import os
from typing import Optional

import requests


_BASE = "https://nubela.co/api/v1"
_TIMEOUT = 15


def _api_key() -> Optional[str]:
    return os.getenv("NINJAPEAR_API_KEY") or os.getenv("PROXYCURL_API_KEY")


def _headers() -> dict:
    k = _api_key()
    if not k:
        return {}
    return {"Authorization": f"Bearer {k}"}


def _skip(reason: str) -> dict:
    return {"ok": False, "data": None, "reason": reason}


def check_disposable_email(email: str) -> dict:
    if not email:
        return _skip("no_email")
    if not _api_key():
        return _skip("missing_api_key")
    try:
        r = requests.get(
            f"{_BASE}/contact/disposable-email",
            params={"email": email},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json(), "reason": ""}
        return _skip(f"http_{r.status_code}")
    except Exception as e:
        return _skip(f"err:{e}")


def fetch_company_logo(website: str) -> dict:
    if not website:
        return _skip("no_website")
    if not _api_key():
        return _skip("missing_api_key")
    try:
        r = requests.get(
            f"{_BASE}/company/logo",
            params={"website": website},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json(), "reason": ""}
        return _skip(f"http_{r.status_code}")
    except Exception as e:
        return _skip(f"err:{e}")


def fetch_company_details(website: str) -> dict:
    """Custo: 2 créditos por chamada bem-sucedida."""
    if not website:
        return _skip("no_website")
    if not _api_key():
        return _skip("missing_api_key")
    try:
        r = requests.get(
            f"{_BASE}/company/details",
            params={"website": website},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json(), "reason": ""}
        return _skip(f"http_{r.status_code}")
    except Exception as e:
        return _skip(f"err:{e}")


def fetch_linkedin_person(linkedin_url: str) -> dict:
    """Custo: 1 crédito."""
    if not linkedin_url:
        return _skip("no_linkedin_url")
    if not _api_key():
        return _skip("missing_api_key")
    try:
        r = requests.get(
            f"{_BASE}/linkedin",
            params={"url": linkedin_url},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return {"ok": True, "data": r.json(), "reason": ""}
        return _skip(f"http_{r.status_code}")
    except Exception as e:
        return _skip(f"err:{e}")
