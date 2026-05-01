# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Product Match – V1.0.0                         │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 12:14         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ product_match.py                               │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Auto-product: seleciona e vincula Setup + Mensalidade ao Deal.

Tier baseado no DealScore (proxy de qualidade/potencial).
Dados calibrados via analyze_won_products.py (477 deals won, 63 com produtos).
"""

from __future__ import annotations

from pd_api import get_deal_products, add_product_to_deal, get_products

# =====================================================
# CONFIGURAÇÃO DE TIERS  (baseado em analyze_won_products.py — 477 deals won)
# =====================================================
# Score < 0  → nenhum produto (lead frio, 354 deals, val_avg=R$68)
#
# Setup (único por deal):
#   Score 0-49  → Setup Lite    (ID 19, R$990,   11 uses, score_avg=90)
#   Score 50-149→ Setup         (ID 26, R$3.500, 12 uses, score_avg=125)
#   Score 150+  → Setup Premium (ID 5,  R$5.900, 19 uses, score_avg=119)
#
# Mensalidade (sempre acompanha o Setup):
#   Score 0-49  → Mensalidade   (ID 27, R$690,   6 uses, score_avg=74)
#   Score 50-149→ Mensalidade   (ID 2,  R$817,  19 uses, score_avg=117)
#   Score 150+  → mensalidade   (ID 24, R$1.308, 32 uses, score_avg=115)

SETUP_TIERS: list[dict] = [
    {"score_min": 0,   "score_max": 49,  "product_id": 19, "item_price": 990,  "label": "Setup Lite"},
    {"score_min": 50,  "score_max": 149, "product_id": 26, "item_price": 3500, "label": "Setup"},
    {"score_min": 150, "score_max": 300, "product_id": 5,  "item_price": 5900, "label": "Setup Premium"},
]

MENSALIDADE_TIERS: list[dict] = [
    {"score_min": 0,   "score_max": 49,  "product_id": 27, "item_price": 690,  "label": "Mensalidade Lite"},
    {"score_min": 50,  "score_max": 149, "product_id": 2,  "item_price": 817,  "label": "Mensalidade"},
    {"score_min": 150, "score_max": 300, "product_id": 24, "item_price": 1308, "label": "Mensalidade Premium"},
]

# Alias para compatibilidade
PRODUCT_TIERS = SETUP_TIERS


def list_available_products() -> list[dict]:
    """Busca e retorna produtos cadastrados no Pipedrive (para configuração)."""
    products = get_products(limit=500)
    return [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "code": p.get("code"),
            "prices": p.get("prices"),
            "active_flag": p.get("active_flag"),
        }
        for p in products
    ]


def _select_tier(tiers: list[dict], score: int) -> dict | None:
    for tier in tiers:
        if tier["score_min"] <= score <= tier["score_max"] and tier.get("product_id"):
            return tier
    return None


def select_product_for_score(score: int) -> dict | None:
    """Retorna o tier de setup adequado para o DealScore dado."""
    return _select_tier(SETUP_TIERS, score)


def assign_product_to_deal(deal_id: int, score: int) -> dict | None:
    """
    Vincula Setup + Mensalidade ao deal baseado no DealScore.
    Retorna info dos produtos vinculados, ou None se:
    - Score < 0 (sem tiers)
    - Deal já tem produto vinculado
    - Nenhum tier match
    """
    setup = _select_tier(SETUP_TIERS, score)
    if not setup:
        return None

    # Verificar se deal já tem produto
    existing = get_deal_products(deal_id)
    if existing:
        return {"skipped": True, "reason": "deal já tem produto", "existing": len(existing)}

    # 1) Vincular Setup
    setup_result = add_product_to_deal(
        deal_id=deal_id,
        product_id=setup["product_id"],
        item_price=setup["item_price"],
    )

    # 2) Vincular Mensalidade
    mensalidade = _select_tier(MENSALIDADE_TIERS, score)
    mens_result = None
    if mensalidade:
        mens_result = add_product_to_deal(
            deal_id=deal_id,
            product_id=mensalidade["product_id"],
            item_price=mensalidade["item_price"],
        )

    return {
        "assigned": True,
        "setup": {"tier": setup["label"], "product_id": setup["product_id"], "price": setup["item_price"]},
        "mensalidade": {"tier": mensalidade["label"], "product_id": mensalidade["product_id"], "price": mensalidade["item_price"]} if mensalidade else None,
        "total_value": setup["item_price"] + (mensalidade["item_price"] if mensalidade else 0),
    }

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
