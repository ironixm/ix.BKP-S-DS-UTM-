"""CNPJ enrichment com fallback chain (BrasilAPI → MinhaReceita → ReceitaWS).

Todas as APIs são gratuitas. ReceitaWS tem rate limit baixo (3 req/min).
"""
import re
import time
from typing import Optional

import requests


_CNPJ_CACHE: dict[str, dict] = {}
_DEFAULT_TIMEOUT = 10


def clean_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj or "")


def is_valid_cnpj(cnpj: str) -> bool:
    """Validação com dígito verificador (algoritmo oficial)."""
    cnpj = clean_cnpj(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def _calc(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights))
        rem = total % 11
        return 0 if rem < 2 else 11 - rem

    d1 = _calc(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _calc(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[12] == str(d1) and cnpj[13] == str(d2)


def _normalize(data: dict, source: str) -> dict:
    """Converte resposta de qualquer fonte para schema unificado."""
    if source == "brasilapi":
        return {
            "cnpj": data.get("cnpj"),
            "razao_social": data.get("razao_social"),
            "nome_fantasia": data.get("nome_fantasia"),
            "email": data.get("email"),
            "telefone": data.get("ddd_telefone_1"),
            "logradouro": data.get("logradouro"),
            "numero": data.get("numero"),
            "complemento": data.get("complemento"),
            "bairro": data.get("bairro"),
            "municipio": data.get("municipio"),
            "uf": data.get("uf"),
            "cep": data.get("cep"),
            "cnae": str(data.get("cnae_fiscal", "")),
            "cnae_descricao": data.get("cnae_fiscal_descricao"),
            "capital_social": data.get("capital_social"),
            "porte": data.get("porte"),
            "situacao": data.get("descricao_situacao_cadastral"),
            "data_inicio": data.get("data_inicio_atividade"),
            "natureza_juridica": data.get("natureza_juridica"),
            "_source": "brasilapi",
        }
    if source == "minhareceita":
        return {
            "cnpj": data.get("cnpj"),
            "razao_social": data.get("razao_social"),
            "nome_fantasia": data.get("nome_fantasia"),
            "email": data.get("email"),
            "telefone": data.get("ddd_telefone_1"),
            "logradouro": data.get("logradouro"),
            "numero": data.get("numero"),
            "bairro": data.get("bairro"),
            "municipio": data.get("municipio"),
            "uf": data.get("uf"),
            "cep": str(data.get("cep") or ""),
            "cnae": str(data.get("cnae_fiscal") or ""),
            "cnae_descricao": data.get("cnae_fiscal_descricao"),
            "capital_social": data.get("capital_social"),
            "porte": data.get("porte"),
            "situacao": data.get("descricao_situacao_cadastral"),
            "_source": "minhareceita",
        }
    if source == "receitaws":
        return {
            "cnpj": clean_cnpj(data.get("cnpj") or ""),
            "razao_social": data.get("nome"),
            "nome_fantasia": data.get("fantasia"),
            "email": data.get("email"),
            "telefone": data.get("telefone"),
            "logradouro": data.get("logradouro"),
            "numero": data.get("numero"),
            "bairro": data.get("bairro"),
            "municipio": data.get("municipio"),
            "uf": data.get("uf"),
            "cep": data.get("cep"),
            "cnae": (data.get("atividade_principal") or [{}])[0].get("code"),
            "cnae_descricao": (data.get("atividade_principal") or [{}])[0].get("text"),
            "capital_social": data.get("capital_social"),
            "porte": data.get("porte"),
            "situacao": data.get("situacao"),
            "_source": "receitaws",
        }
    return {}


def fetch_brasilapi(cnpj: str) -> Optional[dict]:
    cnpj = clean_cnpj(cnpj)
    try:
        r = requests.get(
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
            timeout=_DEFAULT_TIMEOUT,
        )
        if r.status_code == 200:
            return _normalize(r.json(), "brasilapi")
    except Exception as e:
        print(f"[enrichment.brasilapi] erro: {e}", flush=True)
    return None


def fetch_minhareceita(cnpj: str) -> Optional[dict]:
    cnpj = clean_cnpj(cnpj)
    try:
        r = requests.get(
            f"https://minhareceita.org/{cnpj}",
            timeout=_DEFAULT_TIMEOUT,
        )
        if r.status_code == 200:
            return _normalize(r.json(), "minhareceita")
    except Exception as e:
        print(f"[enrichment.minhareceita] erro: {e}", flush=True)
    return None


def fetch_receitaws(cnpj: str) -> Optional[dict]:
    cnpj = clean_cnpj(cnpj)
    try:
        r = requests.get(
            f"https://www.receitaws.com.br/v1/cnpj/{cnpj}",
            timeout=_DEFAULT_TIMEOUT,
        )
        if r.status_code == 200:
            payload = r.json()
            if payload.get("status") != "ERROR":
                return _normalize(payload, "receitaws")
    except Exception as e:
        print(f"[enrichment.receitaws] erro: {e}", flush=True)
    return None


def fetch_cnpj(cnpj: str, *, use_cache: bool = True) -> Optional[dict]:
    """Tenta as 3 fontes em ordem; retorna primeira que responder.

    Resultado em cache de processo (TTL 1h) para evitar re-hits em rajadas.
    """
    cnpj = clean_cnpj(cnpj)
    if not is_valid_cnpj(cnpj):
        return None

    if use_cache:
        cached = _CNPJ_CACHE.get(cnpj)
        if cached and (time.time() - cached["_ts"]) < 3600:
            return cached["data"]

    for fn in (fetch_brasilapi, fetch_minhareceita, fetch_receitaws):
        data = fn(cnpj)
        if data and data.get("razao_social"):
            _CNPJ_CACHE[cnpj] = {"data": data, "_ts": time.time()}
            return data
    return None
