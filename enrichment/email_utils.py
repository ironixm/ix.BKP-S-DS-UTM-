"""Helpers de email e domínio."""
import re
from typing import Optional


# Provedores gratuitos / pessoais (não são "comercial")
FREE_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.com.br",
    "outlook.com", "outlook.com.br", "yahoo.com", "yahoo.com.br",
    "uol.com.br", "bol.com.br", "terra.com.br", "ig.com.br",
    "live.com", "msn.com", "aol.com", "icloud.com", "me.com",
    "protonmail.com", "proton.me", "zoho.com", "ymail.com",
    "mail.com", "globo.com", "oi.com.br", "r7.com",
    "zipmail.com.br", "email.com", "fastmail.com",
}


def get_domain(email: str) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return email.split("@", 1)[1].strip().lower()


def is_commercial_email(email: str) -> bool:
    d = get_domain(email)
    return bool(d) and d not in FREE_DOMAINS


def is_disposable_email_local(email: str) -> bool:
    """Heurística local sem chamar API externa.

    Lista pequena dos descartáveis mais comuns. Para checagem completa,
    usar `ninjapear.check_disposable_email`.
    """
    d = get_domain(email)
    if not d:
        return False
    disposable = {
        "tempmail.com", "10minutemail.com", "mailinator.com",
        "guerrillamail.com", "yopmail.com", "throwaway.email",
        "trashmail.com", "fakeinbox.com", "getnada.com",
        "temp-mail.org", "maildrop.cc", "sharklasers.com",
    }
    return d in disposable


_PHONE_RE = re.compile(r"\D")


def normalize_phone_br(phone: str) -> Optional[str]:
    """Normaliza para formato E.164 BR (+55DDNUMERO)."""
    if not phone:
        return None
    digits = _PHONE_RE.sub("", phone)
    if not digits:
        return None
    if digits.startswith("55") and len(digits) >= 12:
        return "+" + digits
    if len(digits) in (10, 11):  # DDD + número
        return "+55" + digits
    return "+" + digits if len(digits) >= 10 else None
