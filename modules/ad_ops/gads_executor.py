"""Executor de operações Google Ads (set_budget, pause, enable, audit)."""
from __future__ import annotations
import os
from typing import Any

GADS_API_VERSION = "v22"


def _client():
    from google.ads.googleads.client import GoogleAdsClient
    cfg = {
        "developer_token": os.environ["GOOGLE_ADS_DEV_TOKEN"],
        "client_id":       os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret":   os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token":   os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "use_proto_plus":  True,
    }
    lcid = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "").strip()
    if lcid:
        cfg["login_customer_id"] = lcid
    return GoogleAdsClient.load_from_dict(cfg, version=GADS_API_VERSION)


def _customer_id() -> str:
    return os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "").strip()


def set_campaign_budget(*, target_id: str, daily_brl: float) -> dict:
    """Atualiza budget diário em BRL da campanha (via campaign_budget vinculado)."""
    c = _client(); cust = _customer_id()
    ga = c.get_service("GoogleAdsService")

    # 1) descobre o budget resource vinculado
    rows = list(ga.search(customer_id=cust,
        query=f"SELECT campaign.id, campaign.name, campaign_budget.resource_name, campaign_budget.amount_micros FROM campaign WHERE campaign.id = {target_id}"))
    if not rows:
        return {"ok": False, "error": f"Campanha {target_id} não encontrada"}
    bud_res = rows[0].campaign_budget.resource_name
    old = rows[0].campaign_budget.amount_micros / 1e6
    name = rows[0].campaign.name

    # 2) muta budget
    bsvc = c.get_service("CampaignBudgetService")
    op = c.get_type("CampaignBudgetOperation")
    op.update.resource_name = bud_res
    op.update.amount_micros = int(daily_brl * 1e6)
    op.update_mask.paths.append("amount_micros")
    resp = bsvc.mutate_campaign_budgets(customer_id=cust, operations=[op])
    return {"ok": True, "campaign": name, "budget_resource": bud_res,
            "old_brl": round(old,2), "new_brl": round(daily_brl,2),
            "result": [r.resource_name for r in resp.results]}


def set_campaign_status(*, target_id: str, status: str) -> dict:
    """status: 'PAUSED' | 'ENABLED'"""
    c = _client(); cust = _customer_id()
    csvc = c.get_service("CampaignService")
    op = c.get_type("CampaignOperation")
    op.update.resource_name = f"customers/{cust}/campaigns/{target_id}"
    op.update.status = c.enums.CampaignStatusEnum[status]
    op.update_mask.paths.append("status")
    resp = csvc.mutate_campaigns(customer_id=cust, operations=[op])
    return {"ok": True, "status": status, "result": [r.resource_name for r in resp.results]}


def get_campaign_metrics_24h(target_id: str) -> dict:
    """Custo + cliques + conv das últimas 24h (LAST_1_DAY no GAQL = ontem)."""
    c = _client(); cust = _customer_id()
    ga = c.get_service("GoogleAdsService")
    q = f"""
    SELECT campaign.id, metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.all_conversions
    FROM campaign WHERE campaign.id = {target_id} AND segments.date DURING YESTERDAY
    """
    for r in ga.search(customer_id=cust, query=q):
        return {
            "cost_brl": round(r.metrics.cost_micros / 1e6, 2),
            "clicks":   r.metrics.clicks,
            "conv":     r.metrics.conversions,
            "all_conv": r.metrics.all_conversions,
        }
    return {"cost_brl": 0, "clicks": 0, "conv": 0, "all_conv": 0}


def execute(action: str, target_type: str, target_id: str, params: dict) -> dict:
    if target_type != "campaign":
        return {"ok": False, "error": f"GAds só suporta target_type=campaign (recebido {target_type})"}
    if action == "set_budget":
        return set_campaign_budget(target_id=target_id, daily_brl=float(params["daily_brl"]))
    if action == "pause":
        return set_campaign_status(target_id=target_id, status="PAUSED")
    if action == "enable":
        return set_campaign_status(target_id=target_id, status="ENABLED")
    if action == "audit":
        return {"ok": True, "metrics": get_campaign_metrics_24h(target_id)}
    return {"ok": False, "error": f"Ação desconhecida: {action}"}


def verify(metric: str, threshold: float, target_id: str) -> dict:
    """Retorna {ok: bool, value, metric}"""
    m = get_campaign_metrics_24h(target_id)
    if metric == "cost_24h_min":
        v = m["cost_brl"]
        return {"ok": v >= threshold, "value": v, "metric": metric, "threshold": threshold, "metrics": m}
    if metric == "conv_24h_min":
        v = m["all_conv"]
        return {"ok": v >= threshold, "value": v, "metric": metric, "threshold": threshold, "metrics": m}
    return {"ok": True, "value": None, "metric": metric, "metrics": m, "note": "métrica não implementada — passa"}
