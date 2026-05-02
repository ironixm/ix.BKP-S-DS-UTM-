"""Blueprint /madmode."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, render_template, request

from .auth import require_admin
from . import metrics, scheduler

bp = Blueprint("madmode", __name__, url_prefix="/madmode", template_folder="../../templates/madmode")


_TAB_ALIASES = {
    "status": "status", "eventos": "events", "events": "events",
    "deals": "deals", "deals-recentes": "deals", "recentes": "deals",
    "manual": "manual", "manual-run": "manual", "jobs": "manual",
}


_VALID_TABS = {"status","eventos","events","deals","manual","jobs","recentes","enrichment","enrich"}


_TAB_ALIASES = {
    **_TAB_ALIASES,
    "enrichment": "enrichment", "enrich": "enrichment",
}


@bp.route("/")
@bp.route("/<tab>")
@require_admin
def dashboard(tab: str = "status"):
    t = (tab or "").lower()
    if t and t not in _VALID_TABS:
        from flask import abort
        abort(404)
    active = _TAB_ALIASES.get(t, "status")
    return render_template("madmode/dashboard.html", active_tab=active)


@bp.route("/api/overview")
@require_admin
def api_overview():
    return jsonify({
        "overview": metrics.overview(),
        "health": metrics.health_checks(),
        "pool": metrics.pipedrive_pool(),
        "quality": metrics.quality_metrics(),
        "now": datetime.now(timezone.utc).isoformat(),
    })


@bp.route("/api/recent-deals")
@require_admin
def api_recent_deals():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    items = metrics.recent_deals(limit=min(limit, 200), offset=max(0, offset))
    return jsonify({"items": items, "limit": limit, "offset": offset, "count": len(items)})


@bp.route("/api/dedup-stats")
@require_admin
def api_dedup_stats():
    """Índice de duplicação de notas (últimos N dias)."""
    days = int(request.args.get("days", 7))
    try:
        from modules import db as _db
        return jsonify(_db.dedup_stats(days=max(1, min(days, 90))))
    except Exception as e:
        return jsonify({"error": str(e), "deals_scanned": 0, "notes_deleted": 0,
                        "errors": 0, "runs": 0, "duplicate_rate": 0.0, "days": days})


@bp.route("/api/events/series")
@require_admin
def api_events_series():
    hours = int(request.args.get("hours", 24))
    group = request.args.get("group_by", "type")
    return jsonify(metrics.events_series(hours=hours, group_by=group))


@bp.route("/api/events/list")
@require_admin
def api_events_list():
    event_type = request.args.get("type") or None
    source = request.args.get("source") or None
    trigger = request.args.get("trigger") or None
    hours = int(request.args["hours"]) if request.args.get("hours") else None
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    items = metrics.events_filtered(
        event_type=event_type, source=source, trigger=trigger,
        hours=hours, limit=min(limit, 1000), offset=max(0, offset),
    )
    total = metrics.events_count(event_type=event_type, source=source, trigger=trigger, hours=hours)
    return jsonify({"items": items, "total": total, "limit": limit, "offset": offset, "count": len(items)})


@bp.route("/api/events/csv")
@require_admin
def api_events_csv():
    rows = metrics.events_filtered(
        event_type=request.args.get("type") or None,
        source=request.args.get("source") or None,
        trigger=request.args.get("trigger") or None,
        hours=int(request.args["hours"]) if request.args.get("hours") else None,
        limit=int(request.args.get("limit", 50000)),
    )
    keys = sorted({k for r in rows for k in r.keys()})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        # serializa dicts/listas como JSON
        flat = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in r.items()}
        w.writerow(flat)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=madmode_events_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"},
    )


# ----- Scheduler -----

@bp.route("/api/scheduler/jobs", methods=["GET", "POST"])
@require_admin
def api_jobs():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try:
            job = scheduler.create_job(
                batch_size=int(data.get("batch_size", scheduler.PRESET_BATCH_SIZE)),
                freq_minutes=int(data.get("freq_minutes", scheduler.PRESET_FREQ_MIN)),
                date_from=data.get("date_from", ""),
                date_to=data.get("date_to", ""),
                date_field=data.get("date_field", "update_time"),
                with_notes=bool(data.get("with_notes", True)),
                with_prefill=bool(data.get("with_prefill", True)),
                with_dedup=bool(data.get("with_dedup", True)),
                status_filter=data.get("status_filter", "all_not_deleted"),
                sort_dir=data.get("sort_dir", "DESC"),
                cursor_start=int(data.get("cursor_start", 0) or 0),
            )
            return jsonify({"ok": True, "job": job}), 201
        except ValueError as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"jobs": scheduler.list_jobs(), "preset": {
        "batch_size": scheduler.PRESET_BATCH_SIZE,
        "freq_minutes": scheduler.PRESET_FREQ_MIN,
        "daily_limit": scheduler.PIPEDRIVE_DAILY_TOKEN_LIMIT,
        "recommended_max": scheduler.MAX_DAILY_TOKENS_RECOMMENDED,
    }})


@bp.route("/api/scheduler/validate", methods=["POST"])
@require_admin
def api_validate():
    data = request.get_json(silent=True) or {}
    return jsonify(scheduler.validate_config(
        int(data.get("batch_size", 0)),
        int(data.get("freq_minutes", 1)),
    ))


@bp.route("/api/scheduler/jobs/<job_id>", methods=["DELETE"])
@require_admin
def api_delete_job(job_id: str):
    action = request.args.get("action", "cancel")
    if action == "delete":
        return jsonify({"ok": scheduler.delete_job(job_id)})
    return jsonify({"ok": scheduler.cancel_job(job_id)})


@bp.route("/api/scheduler/jobs/<job_id>/resume", methods=["POST"])
@require_admin
def api_resume_job(job_id: str):
    """Reabre um job concluído/cancelado. Body: {reset_cursor: bool}"""
    data = request.get_json(silent=True) or {}
    ok = scheduler.resume_job(job_id, reset_cursor=bool(data.get("reset_cursor")))
    return jsonify({"ok": ok})


@bp.route("/api/scheduler/jobs/<job_id>/errors", methods=["GET"])
@require_admin
def api_job_errors(job_id: str):
    """Retorna eventos de erro associados ao job (scheduler_error/deal_error/dedup_error/quota_pause)."""
    limit = int(request.args.get("limit", 100))
    try:
        from modules import db as _db
        if _db.is_enabled():
            with _db.conn_ctx() as cn, cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ts, type, deal_id, payload
                    FROM events
                    WHERE type LIKE 'scheduler\_%%' ESCAPE '\'
                      AND (payload->>'job_id') = %s
                    ORDER BY ts DESC
                    LIMIT %s
                    """,
                    (job_id, max(1, min(limit, 500))),
                )
                rows = cur.fetchall()
                items = [
                    {
                        "timestamp": r[0].astimezone(timezone.utc).isoformat() if r[0] else None,
                        "type": r[1],
                        "deal_id": r[2],
                        "error": (r[3] or {}).get("error"),
                        "quota_pause_s": (r[3] or {}).get("quota_pause_s"),
                    }
                    for r in rows
                ]
                return jsonify({"job_id": job_id, "items": items, "count": len(items)})
    except Exception as e:
        return jsonify({"job_id": job_id, "items": [], "count": 0, "error": str(e)}), 500
    return jsonify({"job_id": job_id, "items": [], "count": 0})


@bp.route("/api/scheduler/jobs/<job_id>/run-now", methods=["POST"])
@require_admin
def api_run_job_now(job_id: str):
    """Força execução imediata do job (até max_iters batches consecutivos)."""
    data = request.get_json(silent=True) or {}
    iters = int(data.get("max_iters", 1))
    return jsonify(scheduler.run_job_now(job_id, max_iters=iters))


# ----- Prefill DealScore fields -----

@bp.route("/api/prefill/run", methods=["POST"])
@require_admin
def api_prefill_run():
    """Dispara em thread o script de pré-preenchimento dos campos do grupo
    'Deal Score' do Pipedrive. Não bloqueia a request.

    Body JSON:
      {"limit": 200, "dry_run": false, "with_headcount": false,
       "status": "open", "only": "" }
    """
    data = request.get_json(silent=True) or {}
    return jsonify(scheduler.start_prefill(
        limit=int(data.get("limit", 200)),
        dry_run=bool(data.get("dry_run", False)),
        with_headcount=bool(data.get("with_headcount", False)),
        status=str(data.get("status", "open")),
        only=str(data.get("only", "")),
    ))


@bp.route("/api/prefill/status")
@require_admin
def api_prefill_status():
    return jsonify(scheduler.prefill_status())


# ----- Notes Dedup -----

@bp.route("/api/notes/dedup/run", methods=["POST"])
@require_admin
def api_dedup_run():
    """Inicia limpeza de notas duplicadas em background.

    Body JSON opcional: {"deal_id": 9672}  → limpa só esse deal.
    Sem body → modo 'all' (varre todas as notas do Pipedrive).
    """
    data = request.get_json(silent=True) or {}
    return jsonify(scheduler.start_dedup(deal_id=data.get("deal_id")))


@bp.route("/api/notes/dedup/status")
@require_admin
def api_dedup_status():
    return jsonify(scheduler.dedup_status())


@bp.route("/api/notes/dedup/estimate", methods=["POST"])
@require_admin
def api_dedup_estimate():
    """Faz uma estimativa rápida (1 página = 500 notas mais recentes)."""
    data = request.get_json(silent=True) or {}
    pages = max(1, min(int(data.get("pages", 1)), 5))
    try:
        return jsonify(scheduler.estimate_dedup(sample_pages=pages))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----- Debug storage -----

@bp.route("/api/debug/storage")
@require_admin
def api_debug_storage():
    import os
    from pathlib import Path
    info = {
        "ix_data_dir_env": os.environ.get("IX_DATA_DIR", ""),
        "scheduler_jobs_file": str(scheduler.JOBS_FILE),
        "scheduler_jobs_exists": scheduler.JOBS_FILE.exists(),
        "events_log_file": str(metrics.EVENTS_LOG),
        "events_log_exists": metrics.EVENTS_LOG.exists(),
    }
    data_dir = os.environ.get("IX_DATA_DIR", "").strip()
    if data_dir:
        p = Path(data_dir)
        info["data_dir_exists"] = p.exists()
        info["data_dir_is_dir"] = p.is_dir()
        info["data_dir_writable"] = os.access(data_dir, os.W_OK) if p.exists() else False
        try:
            info["data_dir_listing"] = sorted(os.listdir(data_dir))[:20]
        except Exception as e:
            info["data_dir_listing_error"] = str(e)
        # Mount info
        try:
            with open("/proc/mounts") as f:
                all_mounts = [ln.strip() for ln in f]
            info["mounts_match"] = [m for m in all_mounts if data_dir in m]
            info["mounts_count"] = len(all_mounts)
            info["mounts_sample"] = all_mounts[:15]
        except Exception:
            pass
    return jsonify(info)


# ===== Enrichment =====

@bp.route("/api/enrichment/run", methods=["POST"])
@require_admin
def api_enrichment_run():
    """Roda enrichment manualmente. Body JSON: {entity, id, mode?}."""
    from enrichment import enrich_organization, enrich_person
    data = request.get_json(silent=True) or {}
    entity = (data.get("entity") or "").lower()
    eid = data.get("id")
    mode = (data.get("mode") or "auto").lower()
    if entity not in ("organization", "person") or not eid:
        return jsonify({"error": "entity must be organization|person and id required"}), 400
    fn = enrich_organization if entity == "organization" else enrich_person
    try:
        return jsonify(fn(eid, mode=mode))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/enrichment/stats")
@require_admin
def api_enrichment_stats():
    """Stats agregadas dos últimos N eventos enrichment_*."""
    return jsonify(metrics.enrichment_stats(window_hours=int(request.args.get("hours", 168))))


@bp.route("/api/enrichment/sources")
@require_admin
def api_enrichment_sources():
    """Status/cota de cada fonte externa (BrasilAPI, NinjaPear, etc)."""
    from enrichment.sources_status import get_sources_status
    try:
        return jsonify(get_sources_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
