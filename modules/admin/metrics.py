"""Métricas e health checks do painel MadMode.

Lê events.log + faz checks leves nas APIs externas.
Tudo cacheado em memória por TTL curto para não sobrecarregar.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = os.environ.get("IX_DATA_DIR", "").strip()
if _DATA_DIR and os.path.isdir(_DATA_DIR):
    EVENTS_LOG = Path(_DATA_DIR) / "events.log"
else:
    EVENTS_LOG = ROOT / "events.log"

_cache: dict[str, tuple[float, Any]] = {}


def _cached(key: str, ttl: int, fn):
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    val = fn()
    _cache[key] = (now, val)
    return val


def _read_events(max_lines: int = 50000) -> list[dict]:
    """Lê os últimos N eventos. Prioriza Postgres; fallback p/ events.log."""
    # Postgres
    try:
        from modules import db as _db
        if _db.is_enabled():
            evs = _db.fetch_events(limit=max_lines)
            if evs:
                return evs
    except Exception:
        pass
    # Fallback: arquivo
    if not EVENTS_LOG.exists():
        return []
    out: list[dict] = []
    try:
        with EVENTS_LOG.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            chunk = min(size, 4 * 1024 * 1024)
            f.seek(size - chunk)
            data = f.read().decode("utf-8", errors="ignore").splitlines()
            for line in data[-max_lines:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        pass
    return out


# ---------- summary ----------

def _now_utc():
    return datetime.now(timezone.utc)


def _parse_ts(ev: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
    except Exception:
        return None


def overview() -> dict:
    """Snapshot principal do dashboard."""
    return _cached("overview", 30, _build_overview)


def _build_overview() -> dict:
    events = _read_events()
    now = _now_utc()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    deals_24h = set()
    deals_7d = set()
    persons_24h = set()
    score_total_24h = 0
    score_count_24h = 0
    sources_24h = Counter()
    triggers_24h = Counter()
    last_event_ts: datetime | None = None

    for ev in events:
        ts = _parse_ts(ev)
        if not ts:
            continue
        if last_event_ts is None or ts > last_event_ts:
            last_event_ts = ts

        deal_id = ev.get("deal_id")
        person_id = ev.get("person_id")
        etype = ev.get("type")

        if ts >= last_7d and deal_id:
            deals_7d.add(deal_id)
        if ts >= last_24h:
            if deal_id:
                deals_24h.add(deal_id)
            if person_id:
                persons_24h.add(person_id)
            if etype == "deal_score" and "score" in ev:
                score_total_24h += int(ev.get("score") or 0)
                score_count_24h += 1
            if ev.get("source"):
                sources_24h[ev["source"]] += 1
            if etype == "conversion_fired":
                trig = ev.get("trigger") or "?"
                triggers_24h[trig] += 1

    return {
        "deals_24h": len(deals_24h),
        "deals_7d": len(deals_7d),
        "persons_24h": len(persons_24h),
        "avg_score_24h": (score_total_24h / score_count_24h) if score_count_24h else None,
        "scored_24h": score_count_24h,
        "sources_24h": dict(sources_24h),
        "triggers_24h": dict(triggers_24h),
        "last_event_at": last_event_ts.isoformat() if last_event_ts else None,
        "last_event_age_min": (now - last_event_ts).total_seconds() / 60 if last_event_ts else None,
        "events_log_size_kb": EVENTS_LOG.stat().st_size // 1024 if EVENTS_LOG.exists() else 0,
    }


# ---------- quality ----------

def quality_metrics(sample_size: int = 500) -> dict:
    return _cached(f"quality:{sample_size}", 60, lambda: _build_quality(sample_size))


def _build_quality(sample_size: int) -> dict:
    """Amostra deals recentes do Pipedrive e mede qualidade dos dados."""
    try:
        from pd_api import _request
    except Exception as e:
        return {"error": f"pd_api indisponível: {e}"}

    try:
        resp = _request("/deals", params={
            "limit": min(sample_size, 500),
            "start": 0,
            "status": "all_not_deleted",
            "sort": "update_time DESC",
        })
        deals = resp.get("data") or []
    except Exception as e:
        return {"error": str(e)[:120]}

    total = len(deals)
    if not total:
        return {"total_sample": 0}

    have_value = sum(1 for d in deals if d.get("value"))
    have_person = sum(1 for d in deals if d.get("person_id"))
    have_org = sum(1 for d in deals if d.get("org_id"))
    have_stage = sum(1 for d in deals if d.get("stage_id"))
    valid_emails = 0
    valid_phones = 0
    person_sample = 0
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    # Sample person details (cap to avoid quota burn)
    for d in deals[:50]:
        pid = d.get("person_id")
        if isinstance(pid, dict):
            pid = pid.get("value")
        if not pid:
            continue
        try:
            p = _request(f"/persons/{pid}").get("data") or {}
        except Exception:
            continue
        person_sample += 1
        emails = p.get("email") or []
        phones = p.get("phone") or []
        if emails and isinstance(emails[0], dict):
            v = emails[0].get("value", "")
            if EMAIL_RE.match(v or ""):
                valid_emails += 1
        if phones and isinstance(phones[0], dict):
            v = re.sub(r"\D+", "", phones[0].get("value", ""))
            if len(v) >= 10:
                valid_phones += 1

    return {
        "total_sample": total,
        "person_sample": person_sample,
        "pct_with_value": round(100 * have_value / total, 1),
        "pct_with_person": round(100 * have_person / total, 1),
        "pct_with_org": round(100 * have_org / total, 1),
        "pct_with_stage": round(100 * have_stage / total, 1),
        "pct_valid_email": round(100 * valid_emails / person_sample, 1) if person_sample else None,
        "pct_valid_phone": round(100 * valid_phones / person_sample, 1) if person_sample else None,
    }


# ---------- pipedrive pool ----------

def pipedrive_pool() -> dict:
    return _cached("pd_pool", 120, _build_pool)


def _build_pool() -> dict:
    try:
        from pd_api import _request
    except Exception as e:
        return {"error": str(e)}
    out = {}
    for entity, path in (("deals", "/deals"), ("persons", "/persons"), ("organizations", "/organizations")):
        try:
            r = _request(path, params={"limit": 1, "start": 0, "status": "all_not_deleted"} if entity == "deals" else {"limit": 1, "start": 0})
            ad = r.get("additional_data") or {}
            pag = ad.get("pagination") or {}
            # Pipedrive não retorna count total fácil; usa more_items_in_collection + heurística
            out[entity] = {"first_page_count": len(r.get("data") or []), "more": pag.get("more_items_in_collection", False)}
        except Exception as e:
            out[entity] = {"error": str(e)[:80]}
    return out


# ---------- health checks ----------

def health_checks() -> dict:
    return _cached("health", 60, _build_health)


def _build_health() -> dict:
    out = {}
    out["webhooks"] = _check_webhooks()
    out["meta"] = _check_meta()
    out["ga4"] = _check_ga4()
    out["gads"] = _check_gads()
    out["events_log"] = _check_log()
    return out


def _check_log() -> dict:
    # Fonte primária agora é Postgres (events table). Arquivo é fallback.
    try:
        from modules import db as _db
        # Quantos eventos nas últimas 24h?
        with _db.conn_ctx() as c, c.cursor() as cur:
            cur.execute("SELECT COUNT(*), MAX(ts) FROM events WHERE ts > NOW() - INTERVAL '24 hours'")
            cnt, last_ts = cur.fetchone()
        if cnt and cnt > 0:
            age_min = (time.time() - last_ts.timestamp()) / 60 if last_ts else 99999
            return {"ok": True, "source": "postgres", "events_24h": int(cnt), "age_min": round(age_min, 1)}
    except Exception:
        pass
    # Fallback: arquivo
    if not EVENTS_LOG.exists():
        return {"ok": False, "msg": "sem eventos em 24h (PG) e events.log ausente"}
    age_min = (time.time() - EVENTS_LOG.stat().st_mtime) / 60
    return {
        "ok": age_min < 60 * 24,
        "source": "file",
        "size_kb": EVENTS_LOG.stat().st_size // 1024,
        "age_min": round(age_min, 1),
    }


def _check_webhooks() -> dict:
    try:
        from pd_api import _request
        r = _request("/webhooks")
        hooks = r.get("data") or []
        relevant = [h for h in hooks if "bzl.alx-i.com" in (h.get("subscription_url") or "")]
        active = [h for h in relevant if h.get("is_active")]
        return {
            "ok": len(active) > 0,
            "total_pipedrive": len(hooks),
            "ours_total": len(relevant),
            "ours_active": len(active),
            "list": [
                {"id": h.get("id"), "url": h.get("subscription_url"), "event": f"{h.get('event_action')}.{h.get('event_object')}", "active": h.get("is_active"), "version": h.get("version")}
                for h in relevant
            ],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def _check_meta() -> dict:
    pid = os.environ.get("META_PIXEL_ID")
    tok = os.environ.get("META_ACCESS_TOKEN")
    return {"ok": bool(pid and tok), "pixel_id_set": bool(pid), "token_set": bool(tok)}


def _check_ga4() -> dict:
    mid = os.environ.get("GA4_MEASUREMENT_ID")
    sec = os.environ.get("GA4_API_SECRET")
    return {"ok": bool(mid and sec), "measurement_id_set": bool(mid), "secret_set": bool(sec)}


def _check_gads() -> dict:
    keys = ["GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_DEV_TOKEN", "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN",
            "GADS_CONV_DEMO_AGENDADA"]
    missing = [k for k in keys if not os.environ.get(k)]
    return {"ok": not missing, "missing": missing}


# ---------- recent deals ----------

def recent_deals(limit: int = 50, offset: int = 0) -> list[dict]:
    """Últimas atualizações de deal — agrupa por deal_id mantendo o mais recente.

    Lê uma janela maior de eventos do PG (já em DESC) e dedupe mantendo apenas
    o mais novo por deal. Suporta paginação via offset.
    """
    # Pega janela ampla pra ter dados suficientes pós-dedup
    window = max(2000, (offset + limit) * 20)
    events = _read_events(max_lines=window)
    seen = {}
    # events já vêm em ordem DESC (mais recentes primeiro)
    for ev in events:
        if ev.get("type") not in ("deal_score", "conversion_fired"):
            continue
        did = ev.get("deal_id")
        if not did or did in seen:
            continue
        seen[did] = {
            "deal_id": did,
            "person_id": ev.get("person_id"),
            "stage_id": ev.get("stage_id"),
            "score": ev.get("score"),
            "source": ev.get("source"),
            "timestamp": ev.get("timestamp"),
            "url": f"https://web.agendor.com.br/deal/{did}",
        }
    items = list(seen.values())
    return items[offset:offset + limit]


# ---------- events series (chart) ----------

def events_series(hours: int = 24, group_by: str = "type") -> dict:
    """Série temporal por hora dos eventos. group_by ∈ {type, source, trigger}."""
    events = _read_events()
    now = _now_utc()
    cutoff = now - timedelta(hours=hours)
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cats = set()
    for ev in events:
        ts = _parse_ts(ev)
        if not ts or ts < cutoff:
            continue
        bucket = ts.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00")
        if group_by == "source":
            cat = ev.get("source") or "unknown"
        elif group_by == "trigger":
            cat = ev.get("trigger") or "n/a"
        else:
            cat = ev.get("type") or "unknown"
        cats.add(cat)
        buckets[bucket][cat] += 1

    labels = sorted(buckets.keys())
    cats_l = sorted(cats)
    series = [
        {"label": c, "data": [buckets[l].get(c, 0) for l in labels]}
        for c in cats_l
    ]
    return {"labels": labels, "series": series}


# ---------- events filter (list/CSV) ----------

def events_filtered(event_type: str | None = None, source: str | None = None,
                    trigger: str | None = None, hours: int | None = None,
                    limit: int = 5000, offset: int = 0) -> list[dict]:
    # Pede o suficiente pro PG: limit + offset + folga pra filtros descartarem
    fetch_n = max(limit + offset, 200) * (3 if (source or trigger) else 1)
    events = _read_events(max_lines=min(fetch_n, 50000))
    cutoff = _now_utc() - timedelta(hours=hours) if hours else None
    out = []
    skipped = 0
    # events já vêm DESC
    for ev in events:
        if event_type and ev.get("type") != event_type:
            continue
        if source and ev.get("source") != source:
            continue
        if trigger and ev.get("trigger") != trigger:
            continue
        if cutoff:
            ts = _parse_ts(ev)
            if not ts or ts < cutoff:
                continue
        if skipped < offset:
            skipped += 1
            continue
        out.append(ev)
        if len(out) >= limit:
            break
    return out


def events_count(event_type: str | None = None, source: str | None = None,
                 trigger: str | None = None, hours: int | None = None) -> int:
    """Conta total para paginação. Usa PG quando possível."""
    try:
        from modules import db as _db
        if _db.is_enabled() and not source and not trigger:
            since_iso = (_now_utc() - timedelta(hours=hours)).isoformat() if hours else None
            return _db.count_events(type_filter=event_type, since_iso=since_iso)
    except Exception:
        pass
    # Fallback: aproxima carregando até 50k
    evs = _read_events(max_lines=50000)
    cutoff = _now_utc() - timedelta(hours=hours) if hours else None
    n = 0
    for ev in evs:
        if event_type and ev.get("type") != event_type: continue
        if source and ev.get("source") != source: continue
        if trigger and ev.get("trigger") != trigger: continue
        if cutoff:
            ts = _parse_ts(ev)
            if not ts or ts < cutoff: continue
        n += 1
    return n
