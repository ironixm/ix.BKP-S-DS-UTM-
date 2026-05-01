"""Executor Meta Ads via Marketing API (Graph).

Se META_ACCESS_TOKEN não estiver configurado, retorna {ok: False,
awaiting_manual: True} para que a UI mostre instrução manual ao usuário.
"""
from __future__ import annotations
import os, json
from typing import Any
from urllib import request as urlreq, parse, error as urlerr

GRAPH = "https://graph.facebook.com/v21.0"


def _token() -> str | None:
    return (os.environ.get("META_ACCESS_TOKEN") or
            os.environ.get("META_MARKETING_TOKEN") or "").strip() or None


def _api(path: str, method: str = "GET", data: dict | None = None) -> dict:
    tok = _token()
    if not tok:
        return {"ok": False, "awaiting_manual": True,
                "error": "META_ACCESS_TOKEN não configurado — aplicar manualmente"}
    url = f"{GRAPH}{path}"
    body = None
    if data:
        data = {**data, "access_token": tok}
        body = parse.urlencode(data).encode()
    else:
        url += ("&" if "?" in url else "?") + parse.urlencode({"access_token": tok})
    req = urlreq.Request(url, method=method, data=body)
    try:
        with urlreq.urlopen(req, timeout=20) as r:
            return {"ok": True, "data": json.loads(r.read().decode())}
    except urlerr.HTTPError as e:
        return {"ok": False, "error": e.read().decode()[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_adset_budget(*, target_id: str, daily_brl: float) -> dict:
    """target_id = adset id. Budget em centavos (Meta usa unidade mínima da moeda)."""
    cents = int(round(daily_brl * 100))
    return _api(f"/{target_id}", method="POST", data={"daily_budget": cents})


def set_adset_status(*, target_id: str, status: str) -> dict:
    """status: PAUSED | ACTIVE"""
    return _api(f"/{target_id}", method="POST", data={"status": status})


def get_adset_metrics_24h(target_id: str) -> dict:
    r = _api(f"/{target_id}/insights?date_preset=yesterday&fields=spend,clicks,actions")
    if not r.get("ok"):
        return {"cost_brl": 0, "clicks": 0, "conv": 0}
    rows = r["data"].get("data", [])
    if not rows:
        return {"cost_brl": 0, "clicks": 0, "conv": 0}
    row = rows[0]
    spend = float(row.get("spend") or 0)
    clicks = int(row.get("clicks") or 0)
    conv = 0
    for a in row.get("actions") or []:
        if a.get("action_type") in ("submit_application", "schedule", "lead", "purchase"):
            conv += int(float(a.get("value") or 0))
    return {"cost_brl": round(spend, 2), "clicks": clicks, "conv": conv}


def execute(action: str, target_type: str, target_id: str, params: dict) -> dict:
    if target_type != "adset":
        return {"ok": False, "error": f"Meta só suporta adset (recebido {target_type})"}
    if action == "set_budget":
        return set_adset_budget(target_id=target_id, daily_brl=float(params["daily_brl"]))
    if action == "pause":
        return set_adset_status(target_id=target_id, status="PAUSED")
    if action == "enable":
        return set_adset_status(target_id=target_id, status="ACTIVE")
    if action == "audit":
        return {"ok": True, "metrics": get_adset_metrics_24h(target_id)}
    return {"ok": False, "error": f"Ação desconhecida: {action}"}


def verify(metric: str, threshold: float, target_id: str) -> dict:
    m = get_adset_metrics_24h(target_id)
    if metric == "cost_24h_min":
        v = m["cost_brl"]
        return {"ok": v >= threshold, "value": v, "metric": metric, "threshold": threshold, "metrics": m}
    if metric == "conv_24h_min":
        v = m["conv"]
        return {"ok": v >= threshold, "value": v, "metric": metric, "threshold": threshold, "metrics": m}
    return {"ok": True, "value": None, "metric": metric, "metrics": m}
