"""Sources health/quota probes para o painel.

Cada probe retorna:
    {
      "id": "brasilapi",
      "label": "BrasilAPI",
      "enabled": True,      # ENV/feature flag ON
      "ok": True,           # respondeu
      "quota": "unlimited", # texto livre (créditos, rate, etc.)
      "detail": "..."
    }
"""
from __future__ import annotations
import os
import time
import requests

_TIMEOUT = 6


def _flag(name: str, default: str = "ON") -> bool:
    return (os.getenv(name, default) or "").upper() == "ON"


def _probe_brasilapi() -> dict:
    enabled = _flag("ENRICHMENT_ENABLED")
    out = {"id": "brasilapi", "label": "BrasilAPI (CNPJ)", "enabled": enabled, "quota": "free, sem auth"}
    if not enabled:
        out.update(ok=False, detail="ENRICHMENT_ENABLED=OFF")
        return out
    try:
        r = requests.get("https://brasilapi.com.br/api/cnpj/v1/00000000000191", timeout=_TIMEOUT)
        out["ok"] = r.status_code == 200
        out["detail"] = f"HTTP {r.status_code}"
    except Exception as e:
        out["ok"] = False
        out["detail"] = f"erro: {e}"
    return out


def _probe_minhareceita() -> dict:
    enabled = _flag("ENRICHMENT_ENABLED")
    out = {"id": "minhareceita", "label": "MinhaReceita (CNPJ)", "enabled": enabled, "quota": "free"}
    if not enabled:
        out.update(ok=False, detail="ENRICHMENT_ENABLED=OFF")
        return out
    try:
        r = requests.get("https://minhareceita.org/00000000000191", timeout=_TIMEOUT)
        out["ok"] = r.status_code in (200, 429)
        out["detail"] = f"HTTP {r.status_code}"
    except Exception as e:
        out["ok"] = False
        out["detail"] = f"erro: {e}"
    return out


def _probe_receitaws() -> dict:
    enabled = _flag("ENRICHMENT_ENABLED")
    out = {"id": "receitaws", "label": "ReceitaWS (CNPJ fallback)", "enabled": enabled, "quota": "3 req/min free"}
    if not enabled:
        out.update(ok=False, detail="ENRICHMENT_ENABLED=OFF")
        return out
    try:
        r = requests.get("https://receitaws.com.br/v1/cnpj/00000000000191", timeout=_TIMEOUT)
        out["ok"] = r.status_code in (200, 429)
        out["detail"] = f"HTTP {r.status_code}"
    except Exception as e:
        out["ok"] = False
        out["detail"] = f"erro: {e}"
    return out


def _probe_ninjapear() -> dict:
    key = os.getenv("NINJAPEAR_API_KEY") or os.getenv("PROXYCURL_API_KEY")
    enabled = _flag("ENRICHMENT_COMPANY_DETAILS_ENABLED") and bool(key)
    out = {
        "id": "ninjapear",
        "label": "NinjaPear / Proxycurl",
        "enabled": enabled,
        "quota": "—",
    }
    if not key:
        out.update(ok=False, detail="sem NINJAPEAR_API_KEY/PROXYCURL_API_KEY")
        return out
    try:
        r = requests.get(
            "https://nubela.co/proxycurl/api/credit-balance",
            headers={"Authorization": f"Bearer {key}"},
            timeout=_TIMEOUT,
        )
        out["ok"] = r.status_code == 200
        if r.status_code == 200:
            data = r.json()
            credits = data.get("credit_balance") or data.get("credits") or "?"
            out["quota"] = f"{credits} créditos"
            out["detail"] = "OK"
        else:
            out["detail"] = f"HTTP {r.status_code}: {r.text[:80]}"
    except Exception as e:
        out["ok"] = False
        out["detail"] = f"erro: {e}"
    return out


def _probe_google_cse() -> dict:
    key = os.getenv("GOOGLE_CSE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_CX") or "b799e5585cbd040d4"
    enabled = _flag("ENRICHMENT_LINKEDIN_ENABLED") and bool(key)
    out = {
        "id": "google_cse",
        "label": "Google CSE (LinkedIn)",
        "enabled": enabled,
        "quota": "100/dia free",
    }
    if not key:
        out.update(ok=False, detail="sem GOOGLE_CSE_API_KEY")
        return out
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": key, "cx": cx, "q": "test", "num": 1},
            timeout=_TIMEOUT,
        )
        out["ok"] = r.status_code == 200
        if r.status_code == 200:
            out["detail"] = "OK"
        elif r.status_code == 429:
            out["ok"] = False
            out["detail"] = "cota esgotada (429)"
        else:
            out["detail"] = f"HTTP {r.status_code}: {r.text[:80]}"
    except Exception as e:
        out["ok"] = False
        out["detail"] = f"erro: {e}"
    return out


def _probe_whatsapp() -> dict:
    enabled = _flag("ENRICHMENT_WHATSAPP_ENABLED")
    return {
        "id": "whatsapp",
        "label": "WhatsApp Business",
        "enabled": enabled,
        "ok": enabled,
        "quota": "scraping wa.me",
        "detail": "ON" if enabled else "OFF",
    }


def _probe_scraping() -> dict:
    enabled = _flag("ENRICHMENT_SITE_SCRAPING_ENABLED")
    return {
        "id": "site_scraping",
        "label": "Site Scraping (CNPJ)",
        "enabled": enabled,
        "ok": enabled,
        "quota": "—",
        "detail": "ON" if enabled else "OFF",
    }


def get_sources_status() -> dict:
    from concurrent.futures import ThreadPoolExecutor
    started = time.time()
    probes = [
        _probe_brasilapi,
        _probe_minhareceita,
        _probe_receitaws,
        _probe_scraping,
        _probe_ninjapear,
        _probe_google_cse,
        _probe_whatsapp,
    ]
    sources: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(probes)) as ex:
        futs = [ex.submit(p) for p in probes]
        for f in futs:
            try:
                sources.append(f.result(timeout=_TIMEOUT + 2))
            except Exception as e:
                sources.append({"id": "unknown", "label": "?", "enabled": False,
                                "ok": False, "detail": f"erro probe: {e}"})
    return {
        "sources": sources,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
