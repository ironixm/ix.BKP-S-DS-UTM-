"""Scraping de website para descobrir CNPJ.

Tenta extrair CNPJ de páginas comuns (`/`, `/contato`, `/sobre`, `/footer`,
`/institucional`, `/empresa`). Usa regex padrão de CNPJ formatado.
"""
import re
import time
from typing import Optional

import requests

from .cnpj import is_valid_cnpj, clean_cnpj


_CNPJ_REGEX = re.compile(r"\d{2}[\.\s]?\d{3}[\.\s]?\d{3}/?\d{4}-?\d{2}")
_PATHS = ["", "/contato", "/contact", "/sobre", "/about",
          "/institucional", "/empresa", "/quem-somos", "/sobre-nos",
          "/politica-de-privacidade", "/termos-de-uso", "/footer"]
_DEFAULT_TIMEOUT = 8
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ix-enrichment/1.0; +https://ironix.com.br)"
}


def find_cnpj_in_text(text: str) -> Optional[str]:
    if not text:
        return None
    for m in _CNPJ_REGEX.findall(text):
        candidate = clean_cnpj(m)
        if is_valid_cnpj(candidate):
            return candidate
    return None


def scrape_cnpj_from_domain(domain: str, *, max_pages: int = 6) -> Optional[str]:
    """Tenta achar CNPJ válido em até `max_pages` URLs do domínio.

    Retorna o primeiro CNPJ válido encontrado, ou None.
    """
    if not domain:
        return None
    domain = domain.strip().lower()
    if not domain.startswith(("http://", "https://")):
        base = f"https://{domain}"
    else:
        base = domain

    tried = 0
    for path in _PATHS:
        if tried >= max_pages:
            break
        url = base + path
        try:
            r = requests.get(url, timeout=_DEFAULT_TIMEOUT,
                             headers=_HEADERS, allow_redirects=True)
            tried += 1
            if r.status_code != 200:
                continue
            cnpj = find_cnpj_in_text(r.text)
            if cnpj:
                print(f"[enrichment.scrape] CNPJ {cnpj} em {url}", flush=True)
                return cnpj
        except Exception as e:
            print(f"[enrichment.scrape] erro {url}: {e}", flush=True)
        # politidez
        time.sleep(0.3)
    return None
