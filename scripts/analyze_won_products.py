# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Analyze Won Products – V1.0.0                  │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 10:15         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/analyze_won_products.py                │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Analisa produtos vinculados a deals WON do último ano.
Objetivo: descobrir quais produtos foram fechados, a que preço,
e mapear a relação produto × DealScore para configurar PRODUCT_TIERS.

Uso: PIPEDRIVE_API_KEY=xxx python scripts/analyze_won_products.py
"""
import os
import sys
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pd_api import _request, get_deal_products, get_deal
from dealscore.deal_score import compute_deal_score, FIELD_IDS


DEALSCORE_FIELD = "6ecee6457426bc4cc8f2fcce89b14baf3793ecfe"


def fetch_won_deals(limit_per_page=100, max_pages=20):
    """Busca todos os deals com status=won, paginando."""
    all_deals = []
    start = 0
    for _ in range(max_pages):
        j = _request("/deals", params={
            "status": "won",
            "start": start,
            "limit": limit_per_page,
            "sort": "won_time DESC",
        })
        data = j.get("data") or []
        all_deals.extend(data)
        pagination = j.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection"):
            break
        start = pagination.get("next_start", start + limit_per_page)
        time.sleep(0.2)
    return all_deals


def main():
    print("=== ANÁLISE: Produtos em Deals Won (último ano) ===\n")

    cutoff = datetime.now() - timedelta(days=365)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    print(f"Buscando deals won desde {cutoff_str}...\n")

    all_won = fetch_won_deals()
    print(f"Total de deals won encontrados: {len(all_won)}")

    # Filtrar último ano
    recent = []
    for d in all_won:
        won_time = d.get("won_time") or d.get("close_time") or ""
        if won_time >= cutoff_str:
            recent.append(d)
    print(f"Deals won no último ano: {len(recent)}\n")

    # Analisar produtos de cada deal
    product_stats = defaultdict(lambda: {
        "name": "",
        "count": 0,
        "total_value": 0.0,
        "prices": [],
        "deal_scores": [],
        "deal_names": [],
    })

    deals_with_products = 0
    deals_without_products = 0
    deal_values = []  # (deal_value, deal_score, products_attached)

    for i, deal in enumerate(recent):
        deal_id = deal["id"]
        title = deal.get("title", "?")
        deal_value = deal.get("value") or 0
        deal_score = deal.get(DEALSCORE_FIELD) or 0

        try:
            deal_score = int(deal_score)
        except (ValueError, TypeError):
            deal_score = 0

        # Buscar produtos desse deal
        try:
            products = get_deal_products(deal_id)
        except Exception:
            products = []
        time.sleep(0.15)

        if products:
            deals_with_products += 1
            for p in products:
                pid = p.get("product_id")
                pname = p.get("name") or (p.get("product") or {}).get("name", "?")
                pprice = p.get("item_price") or 0
                qty = p.get("quantity") or 1

                stats = product_stats[pid]
                stats["name"] = pname
                stats["count"] += 1
                stats["total_value"] += float(pprice) * float(qty)
                stats["prices"].append(float(pprice))
                stats["deal_scores"].append(deal_score)
                stats["deal_names"].append(title[:40])
        else:
            deals_without_products += 1

        deal_values.append({
            "deal_id": deal_id,
            "title": title[:50],
            "value": float(deal_value),
            "score": deal_score,
            "products": len(products),
            "product_names": [p.get("name", "?") for p in products],
        })

        if (i + 1) % 20 == 0 or i == len(recent) - 1:
            print(f"  Analisados: {i+1}/{len(recent)}")

    # =====================================================
    # RELATÓRIO
    # =====================================================
    print("\n" + "=" * 70)
    print("  RELATÓRIO: PRODUTOS EM DEALS WON (ÚLTIMO ANO)")
    print("=" * 70)

    print(f"\n  Deals com produto: {deals_with_products}")
    print(f"  Deals sem produto: {deals_without_products}")
    print(f"  Total analisados:  {len(recent)}")

    # --- Tabela de Produtos ---
    print(f"\n{'─' * 70}")
    print(f"  {'ID':>6}  {'Produto':<30}  {'Qtd':>4}  {'Preço Médio':>12}  {'Total':>12}")
    print(f"{'─' * 70}")

    for pid, stats in sorted(product_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        avg_price = sum(stats["prices"]) / len(stats["prices"]) if stats["prices"] else 0
        pid_str = str(pid) if pid else "?"
        print(
            f"  {pid_str:>6}  {stats['name'][:30]:<30}  {stats['count']:>4}  "
            f"R${avg_price:>10,.2f}  R${stats['total_value']:>10,.2f}"
        )
        if stats["deal_scores"]:
            scores = stats["deal_scores"]
            avg_s = sum(scores) / len(scores)
            min_s = min(scores)
            max_s = max(scores)
            print(f"          DealScore: avg={avg_s:.0f}  min={min_s}  max={max_s}")

    # --- Distribuição por faixa de valor ---
    print(f"\n{'─' * 70}")
    print("  DISTRIBUIÇÃO DE DEAL VALUE (deals won)")
    print(f"{'─' * 70}")

    faixas = [
        (0, 0, "R$0 (sem valor)"),
        (0.01, 999, "R$0–R$999"),
        (1000, 4999, "R$1K–R$5K"),
        (5000, 14999, "R$5K–R$15K"),
        (15000, 49999, "R$15K–R$50K"),
        (50000, float("inf"), "R$50K+"),
    ]

    for lo, hi, label in faixas:
        matches = [d for d in deal_values if lo <= d["value"] <= hi]
        if matches:
            scores = [d["score"] for d in matches]
            avg_s = sum(scores) / len(scores) if scores else 0
            print(f"  {label:<20}  {len(matches):>3} deals  score_avg={avg_s:.0f}")

    # --- Top 20 deals por valor ---
    print(f"\n{'─' * 70}")
    print("  TOP 20 DEALS WON POR VALOR")
    print(f"{'─' * 70}")
    top = sorted(deal_values, key=lambda d: d["value"], reverse=True)[:20]
    for d in top:
        prods = ", ".join(d["product_names"]) if d["product_names"] else "—"
        print(
            f"  R${d['value']:>10,.2f}  score={d['score']:>4}  "
            f"{d['title'][:35]:<35}  prods: {prods[:40]}"
        )

    # --- Score vs Value correlation ---
    print(f"\n{'─' * 70}")
    print("  DEALSCORE × VALOR (faixas de score)")
    print(f"{'─' * 70}")

    score_faixas = [
        (-100, 0,   "🪨 Morto/Frio"),
        (1,    50,  "🌱 Semente"),
        (51,   100, "🌿 Crescendo"),
        (101,  200, "🌳 Alta prioridade"),
        (201,  300, "🍀 Estratégico"),
    ]
    for lo, hi, label in score_faixas:
        matches = [d for d in deal_values if lo <= d["score"] <= hi]
        if matches:
            values = [d["value"] for d in matches]
            avg_v = sum(values) / len(values)
            med_v = sorted(values)[len(values) // 2]
            max_v = max(values)
            print(
                f"  {label:<16}  {len(matches):>3} deals  "
                f"val_avg=R${avg_v:>10,.2f}  med=R${med_v:>10,.2f}  max=R${max_v:>10,.2f}"
            )

    # --- Salvar JSON completo ---
    output = {
        "generated_at": datetime.now().isoformat(),
        "cutoff": cutoff_str,
        "total_won": len(recent),
        "with_products": deals_with_products,
        "without_products": deals_without_products,
        "products": {
            str(pid): {
                "name": s["name"],
                "count": s["count"],
                "avg_price": sum(s["prices"]) / len(s["prices"]) if s["prices"] else 0,
                "total_value": s["total_value"],
                "score_avg": sum(s["deal_scores"]) / len(s["deal_scores"]) if s["deal_scores"] else 0,
                "score_min": min(s["deal_scores"]) if s["deal_scores"] else 0,
                "score_max": max(s["deal_scores"]) if s["deal_scores"] else 0,
            } for pid, s in product_stats.items()
        },
        "deals": deal_values,
    }

    out_path = os.path.join(os.path.dirname(__file__), "won_products_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Dados completos salvos em: {out_path}")
    print()


if __name__ == "__main__":
    main()

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
