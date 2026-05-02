"""WhatsApp Business check via wa.me scraping (sem custo).

Detecta se o número tem perfil WA Business pela presença de catálogo/perfil.
Best-effort — Meta pode mudar o markup a qualquer momento.
"""
import re
from typing import Optional

import requests


_TIMEOUT = 8
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ix-enrichment/1.0)",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def check_whatsapp_business(phone: str) -> dict:
    """Retorna {has_whatsapp, is_business, catalog_url, profile_pic}."""
    if not phone:
        return {"ok": False, "reason": "no_phone"}
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        return {"ok": False, "reason": "invalid_phone"}
    if not digits.startswith("55"):
        digits = "55" + digits

    url = f"https://wa.me/{digits}"
    try:
        r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS,
                         allow_redirects=True)
        if r.status_code != 200:
            return {"ok": False, "reason": f"http_{r.status_code}"}
        body = r.text
        has_wa = (
            'action="https://api.whatsapp.com/send' in body
            or "Continuar para o chat" in body
            or "Continue to Chat" in body
        )
        catalog = f"https://wa.me/c/{digits}" if 'data-phone-number' in body else None
        return {
            "ok": True,
            "data": {
                "has_whatsapp": has_wa,
                "catalog_url": catalog,
                "profile_url": url,
            },
            "reason": "",
        }
    except Exception as e:
        return {"ok": False, "reason": f"err:{e}"}
