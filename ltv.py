# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Ltv – V1.0.0                                   │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 15:09         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ ltv.py                                         │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
LTV: calcula e preenche Tenure, LTV e ConversionValue no deal.

Regra de ouro: NUNCA sobrescreve valor já definido manualmente.
Se o campo já tem valor > 0, mantém o existente.

Fórmulas:
  Tenure     = 12 (meses, default)
  LTV        = Setup + (Mensalidade × Tenure)
  ConvValue  = LTV  (valor enviado para Meta/Google/Analytics)
"""
from __future__ import annotations

from mappings import DEAL_TENURE_KEY, DEAL_LTV_KEY, DEAL_CONVERSION_VALUE_KEY
from product_match import _select_tier, SETUP_TIERS, MENSALIDADE_TIERS

DEFAULT_TENURE_MONTHS = 12


def compute_ltv(score: int, tenure_months: int = DEFAULT_TENURE_MONTHS) -> dict | None:
    """Calcula LTV baseado no tier de produto para o DealScore dado.

    Returns dict com tenure, setup, mensalidade, ltv, conversion_value
    ou None se score < 0 (sem tier).
    """
    setup = _select_tier(SETUP_TIERS, score)
    if not setup:
        return None

    mensalidade = _select_tier(MENSALIDADE_TIERS, score)
    mens_price = mensalidade["item_price"] if mensalidade else 0

    ltv = setup["item_price"] + (mens_price * tenure_months)

    return {
        "tenure": tenure_months,
        "setup_price": setup["item_price"],
        "setup_label": setup["label"],
        "mensalidade_price": mens_price,
        "mensalidade_label": mensalidade["label"] if mensalidade else None,
        "ltv": ltv,
        "conversion_value": ltv,
    }


def build_ltv_payload(deal: dict, score: int) -> dict:
    """Constrói payload de atualização do deal com tenure/LTV/ConversionValue.

    Respeita valores já preenchidos: se o campo já tem valor > 0, não sobrescreve.
    """
    ltv_data = compute_ltv(score)
    if not ltv_data:
        return {}

    payload = {}

    # Tenure — só preenche se vazio/zero
    existing_tenure = deal.get(DEAL_TENURE_KEY)
    if not existing_tenure or float(existing_tenure) == 0:
        payload[DEAL_TENURE_KEY] = ltv_data["tenure"]
    else:
        # Recalcula LTV usando tenure existente (que pode ter sido ajustado manualmente)
        ltv_data = compute_ltv(score, tenure_months=int(float(existing_tenure)))

    # LTV — só preenche se vazio/zero
    existing_ltv = deal.get(DEAL_LTV_KEY)
    if not existing_ltv or float(existing_ltv) == 0:
        payload[DEAL_LTV_KEY] = ltv_data["ltv"]

    # ConversionValue — só preenche se vazio/zero
    existing_cv = deal.get(DEAL_CONVERSION_VALUE_KEY)
    if not existing_cv or float(existing_cv) == 0:
        payload[DEAL_CONVERSION_VALUE_KEY] = ltv_data["conversion_value"]

    return payload

'''
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
'''
