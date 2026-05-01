# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Analyze Ltv – V1.0.0                           │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 12:18         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/analyze_ltv.py                         │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Analisa tempo de permanência (tenure) de clientes e calcula LTV.

Abordagem:
1. Busca TODOS os deals (won + lost) agrupados por organização
2. Para cada org: primeiro won_time → último lost_time (ou hoje) = tenure
3. Soma valor de todos os deals daquela org = receita total
4. LTV = receita acumulada por org, com tenure médio

Uso: PIPEDRIVE_API_KEY=xxx python scripts/analyze_ltv.py
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

from pd_api import _request

TODAY = datetime.now()
DEALSCORE_FIELD = "6ecee6457426bc4cc8f2fcce89b14baf3793ecfe"


def fetch_all_deals(status="all_not_deleted", limit_per_page=100, max_pages=50):
    """Busca todos os deals paginando."""
    all_deals = []
    start = 0
    for _ in range(max_pages):
        j = _request("/deals", params={
            "status": status,
            "start": start,
            "limit": limit_per_page,
        })
        data = j.get("data") or []
        all_deals.extend(data)
        pagination = j.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection"):
            break
        start = pagination.get("next_start", start + limit_per_page)
        time.sleep(0.15)
    return all_deals


def parse_dt(s):
    """Parse datetime string do Pipedrive."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+00:00", ""))
    except (ValueError, TypeError):
        return None


def months_between(dt1, dt2):
    """Retorna meses entre duas datas (float)."""
    delta = dt2 - dt1
    return max(delta.days / 30.44, 0)


def main():
    print("=" * 70)
    print("  ANÁLISE DE TENURE E LTV — Deals Pipedrive")
    print("=" * 70)
    print()

    # 1) Buscar deals won e lost
    print("Buscando deals won...")
    won_deals = fetch_all_deals(status="won")
    print(f"  {len(won_deals)} deals won")

    print("Buscando deals lost...")
    lost_deals = fetch_all_deals(status="lost")
    print(f"  {len(lost_deals)} deals lost")

    print("Buscando deals open...")
    open_deals = fetch_all_deals(status="open")
    print(f"  {len(open_deals)} deals open")

    all_deals = won_deals + lost_deals + open_deals
    print(f"\nTotal: {len(all_deals)} deals")

    # 2) Agrupar por organização
    orgs = defaultdict(lambda: {
        "name": "Sem organização",
        "deals": [],
        "won_deals": [],
        "lost_deals": [],
        "open_deals": [],
        "first_won": None,
        "last_activity": None,
        "churned": False,
        "churn_date": None,
        "total_value": 0.0,
    })

    no_org_count = 0
    for d in all_deals:
        org_id = d.get("org_id")
        if isinstance(org_id, dict):
            org_id = org_id.get("value")
        if not org_id:
            org_name = (d.get("org_name") or
                        (d.get("org_id") or {}).get("name") if isinstance(d.get("org_id"), dict) else None)
            if not org_name:
                no_org_count += 1
                continue
            # Usar nome como chave fallback
            org_id = f"name:{org_name}"

        org_name = ""
        if isinstance(d.get("org_id"), dict):
            org_name = d["org_id"].get("name", "")
        elif d.get("org_name"):
            org_name = d["org_name"]
        if org_name:
            orgs[org_id]["name"] = org_name

        orgs[org_id]["deals"].append(d)
        status = d.get("status", "")
        val = float(d.get("value") or 0)

        if status == "won":
            orgs[org_id]["won_deals"].append(d)
            orgs[org_id]["total_value"] += val
            wt = parse_dt(d.get("won_time"))
            if wt:
                if orgs[org_id]["first_won"] is None or wt < orgs[org_id]["first_won"]:
                    orgs[org_id]["first_won"] = wt
                if orgs[org_id]["last_activity"] is None or wt > orgs[org_id]["last_activity"]:
                    orgs[org_id]["last_activity"] = wt
        elif status == "lost":
            orgs[org_id]["lost_deals"].append(d)
            lt = parse_dt(d.get("lost_time"))
            if lt:
                if orgs[org_id]["last_activity"] is None or lt > orgs[org_id]["last_activity"]:
                    orgs[org_id]["last_activity"] = lt
        elif status == "open":
            orgs[org_id]["open_deals"].append(d)

    print(f"\nOrganizações com deals: {len(orgs)}")
    print(f"Deals sem organização (ignorados): {no_org_count}")

    # 3) Calcular tenure por organização (apenas as que tiveram deal won)
    orgs_with_won = {oid: info for oid, info in orgs.items() if info["won_deals"]}
    print(f"Organizações com pelo menos 1 deal won: {len(orgs_with_won)}")

    tenure_data = []
    for oid, info in orgs_with_won.items():
        first_won = info["first_won"]
        if not first_won:
            continue

        # Determinar se churn: tem deal lost DEPOIS do won e nenhum open/won recente
        has_open = len(info["open_deals"]) > 0
        latest_lost = None
        for ld in info["lost_deals"]:
            lt = parse_dt(ld.get("lost_time"))
            if lt and lt > first_won:
                if latest_lost is None or lt > latest_lost:
                    latest_lost = lt

        # Determinar data de referência para tenure
        if latest_lost and not has_open:
            # Provável churn: último lost após o won
            end_date = latest_lost
            churned = True
        else:
            # Cliente ativo (ou sem dados de churn)
            end_date = TODAY
            churned = False

        tenure_months = months_between(first_won, end_date)

        # Calcular mensalidade média (valor total / tenure em meses)
        mrr = info["total_value"] / max(tenure_months, 1)

        tenure_data.append({
            "org_id": oid,
            "org_name": info["name"],
            "n_won": len(info["won_deals"]),
            "n_lost": len(info["lost_deals"]),
            "n_open": len(info["open_deals"]),
            "total_value": info["total_value"],
            "first_won": first_won.isoformat(),
            "end_date": end_date.isoformat(),
            "tenure_months": round(tenure_months, 1),
            "churned": churned,
            "mrr_estimated": round(mrr, 2),
        })

    # 4) Análise estatística
    tenures = [t["tenure_months"] for t in tenure_data if t["tenure_months"] > 0]
    churned = [t for t in tenure_data if t["churned"]]
    active = [t for t in tenure_data if not t["churned"]]

    churned_tenures = [t["tenure_months"] for t in churned if t["tenure_months"] > 0]
    active_tenures = [t["tenure_months"] for t in active if t["tenure_months"] > 0]

    def stats(arr, label):
        if not arr:
            print(f"  {label}: sem dados")
            return
        arr_sorted = sorted(arr)
        n = len(arr_sorted)
        avg = sum(arr_sorted) / n
        median = arr_sorted[n // 2]
        p25 = arr_sorted[n // 4] if n > 3 else arr_sorted[0]
        p75 = arr_sorted[3 * n // 4] if n > 3 else arr_sorted[-1]
        print(f"  {label}:")
        print(f"    N={n}  avg={avg:.1f}m  median={median:.1f}m  P25={p25:.1f}m  P75={p75:.1f}m  min={arr_sorted[0]:.1f}m  max={arr_sorted[-1]:.1f}m")

    print()
    print("─" * 70)
    print("  TENURE (tempo de permanência em meses)")
    print("─" * 70)
    stats(tenures, "Todos")
    stats(active_tenures, "Ativos (ainda sem churn)")
    stats(churned_tenures, "Churned")

    # 5) Distribuição por faixa de tenure
    faixas = [
        (0, 3, "0–3 meses"),
        (3, 6, "3–6 meses"),
        (6, 12, "6–12 meses"),
        (12, 24, "12–24 meses"),
        (24, 999, "24+ meses"),
    ]

    print()
    print("─" * 70)
    print("  DISTRIBUIÇÃO POR FAIXA DE TENURE")
    print("─" * 70)
    for lo, hi, label in faixas:
        in_range = [t for t in tenure_data if lo <= t["tenure_months"] < hi]
        ch = sum(1 for t in in_range if t["churned"])
        ac = sum(1 for t in in_range if not t["churned"])
        vals = [t["total_value"] for t in in_range]
        avg_val = sum(vals) / len(vals) if vals else 0
        print(f"  {label:15s}  {len(in_range):>4} orgs  ({ac} ativos, {ch} churned)  val_avg=R${avg_val:>10,.2f}")

    # 6) LTV estimado
    print()
    print("─" * 70)
    print("  LTV ESTIMADO")
    print("─" * 70)

    # LTV = ARPU médio (valor won / org) × tenure médio
    values = [t["total_value"] for t in tenure_data if t["total_value"] > 0]
    avg_value = sum(values) / len(values) if values else 0
    avg_tenure = sum(tenures) / len(tenures) if tenures else 0
    avg_churned_tenure = sum(churned_tenures) / len(churned_tenures) if churned_tenures else 0

    # Churn rate estimado
    total_org = len(tenure_data)
    churn_count = len(churned)
    churn_rate = churn_count / total_org if total_org else 0

    # MRR médio dos que têm valor
    mrrs = [t["mrr_estimated"] for t in tenure_data if t["total_value"] > 0 and t["tenure_months"] > 1]
    avg_mrr = sum(mrrs) / len(mrrs) if mrrs else 0

    print(f"  Organizações com deals won: {total_org}")
    print(f"  Ativos: {len(active)}  |  Churned: {churn_count}  |  Churn rate: {churn_rate:.1%}")
    print(f"  Tenure médio (churned): {avg_churned_tenure:.1f} meses")
    print(f"  Tenure médio (ativos): {sum(active_tenures)/len(active_tenures):.1f} meses" if active_tenures else "  Tenure médio (ativos): N/A")
    print(f"  Valor médio por org (receita won total): R${avg_value:,.2f}")
    print(f"  MRR estimado médio (valor/tenure): R${avg_mrr:,.2f}")
    print()
    print(f"  ⭐ LTV estimado (valor médio por org): R${avg_value:,.2f}")
    print(f"  ⭐ LTV via MRR×tenure churned: R${avg_mrr * avg_churned_tenure:,.2f}" if avg_churned_tenure else "  ⭐ LTV via MRR×tenure: sem dados de churn suficientes")

    # 7) Top orgs por valor
    print()
    print("─" * 70)
    print("  TOP 20 ORGANIZAÇÕES POR RECEITA TOTAL")
    print("─" * 70)
    top_val = sorted(tenure_data, key=lambda t: -t["total_value"])[:20]
    for t in top_val:
        status = "CHURN" if t["churned"] else "ATIVO"
        print(f"  R${t['total_value']:>10,.2f}  {t['tenure_months']:>5.1f}m  {status:5s}  {t['org_name'][:40]}")

    # 8) Salvar JSON
    output = {
        "generated_at": TODAY.isoformat(),
        "summary": {
            "total_orgs_with_won": total_org,
            "active": len(active),
            "churned": churn_count,
            "churn_rate": round(churn_rate, 4),
            "avg_tenure_all": round(avg_tenure, 1),
            "avg_tenure_churned": round(avg_churned_tenure, 1),
            "avg_tenure_active": round(sum(active_tenures) / len(active_tenures), 1) if active_tenures else None,
            "avg_value_per_org": round(avg_value, 2),
            "avg_mrr": round(avg_mrr, 2),
            "ltv_direct": round(avg_value, 2),
            "ltv_mrr_tenure": round(avg_mrr * avg_churned_tenure, 2) if avg_churned_tenure else None,
        },
        "tenure_distribution": [
            {
                "range": label,
                "count": len([t for t in tenure_data if lo <= t["tenure_months"] < hi]),
                "active": sum(1 for t in tenure_data if lo <= t["tenure_months"] < hi and not t["churned"]),
                "churned": sum(1 for t in tenure_data if lo <= t["tenure_months"] < hi and t["churned"]),
            }
            for lo, hi, label in faixas
        ],
        "organizations": sorted(tenure_data, key=lambda t: -t["total_value"]),
    }

    out_path = os.path.join(os.path.dirname(__file__), "ltv_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Dados completos salvos em: {out_path}")


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
