"""Blueprint /madmode/ad-ops — UI + API de operações de mídia agendadas."""
from __future__ import annotations
from datetime import datetime, timezone
from flask import Blueprint, jsonify, render_template, request

from modules.admin.auth import require_admin
from . import store, scheduler

bp = Blueprint("ad_ops", __name__, url_prefix="/madmode/ad-ops",
               template_folder="../../templates/madmode")


def _parse_dt(s: str | None) -> datetime | None:
    if not s: return None
    try:
        if s.endswith("Z"): s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return None


@bp.route("/")
@require_admin
def page():
    return render_template("madmode/ad_ops.html")


@bp.route("/api/ops", methods=["GET"])
@require_admin
def list_ops():
    status = request.args.get("status") or None
    channel = request.args.get("channel") or None
    return jsonify({"ok": True, "ops": store.list_ops(status=status, channel=channel, limit=500)})


@bp.route("/api/ops", methods=["POST"])
@require_admin
def create_op():
    p = request.get_json(force=True) or {}
    required = ["channel", "action", "target_type", "target_name"]
    miss = [k for k in required if not p.get(k)]
    if miss:
        return jsonify({"ok": False, "error": f"missing: {miss}"}), 400
    oid = store.enqueue(
        channel=p["channel"], action=p["action"],
        target_type=p["target_type"], target_id=p.get("target_id"),
        target_name=p["target_name"], params=p.get("params") or {},
        scheduled_for=_parse_dt(p.get("scheduled_for")),
        depends_on=p.get("depends_on"),
        verify_after_min=p.get("verify_after_min"),
        verify_metric=p.get("verify_metric"),
        verify_threshold=p.get("verify_threshold"),
        on_success=p.get("on_success"), on_failure=p.get("on_failure"),
        note=p.get("note"),
    )
    return jsonify({"ok": True, "id": oid, "op": store.get_op(oid)})


@bp.route("/api/ops/bulk", methods=["POST"])
@require_admin
def create_bulk():
    p = request.get_json(force=True) or {}
    ops = p.get("ops") or []
    created = []
    for o in ops:
        try:
            oid = store.enqueue(
                channel=o["channel"], action=o["action"],
                target_type=o["target_type"], target_id=o.get("target_id"),
                target_name=o["target_name"], params=o.get("params") or {},
                scheduled_for=_parse_dt(o.get("scheduled_for")),
                depends_on=o.get("depends_on"),
                verify_after_min=o.get("verify_after_min"),
                verify_metric=o.get("verify_metric"),
                verify_threshold=o.get("verify_threshold"),
                on_success=o.get("on_success"), on_failure=o.get("on_failure"),
                note=o.get("note"),
                op_id=o.get("id"),
            )
            created.append(oid)
        except Exception as e:
            created.append({"error": str(e)})
    return jsonify({"ok": True, "count": len(created), "ids": created})


@bp.route("/api/ops/<op_id>/cancel", methods=["POST"])
@require_admin
def cancel(op_id: str):
    return jsonify({"ok": store.cancel_op(op_id)})


@bp.route("/api/ops/<op_id>/run-now", methods=["POST"])
@require_admin
def run_now(op_id: str):
    # Permite re-executar ops failed/cancelled resetando para pending
    op = store.get_op(op_id)
    if op and op["status"] in (store.OP_STATUS_FAILED, store.OP_STATUS_CANCELLED):
        store.update_op(op_id, status=store.OP_STATUS_PENDING, result=None, executed_at=None)
    return jsonify(scheduler.run_now(op_id))


@bp.route("/api/ops/<op_id>", methods=["GET"])
@require_admin
def get_one(op_id: str):
    op = store.get_op(op_id)
    return jsonify({"ok": bool(op), "op": op})


@bp.route("/api/seed-blz-may26", methods=["POST"])
def seed_blz_may26():
    """Seed do plano BuzzLead R$18k/mês (GAds + Meta).
    Auth: header X-Seed-Token == env ADMIN_PASS (one-shot manual).
    """
    import os as _os
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    tok = request.headers.get("X-Seed-Token", "")
    if not tok or tok != (_os.environ.get("ADMIN_PASS") or ""):
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    now = _dt.now(_tz.utc)
    in_5d = now + _td(days=5)

    plan = [
        # === GAds ===
        # PMax: 82 → 200 agora; verifica cost_24h ≥ 180 em 5d → escala 200→360
        {"id": "blz-pmax-200", "channel": "gads", "action": "set_budget",
         "target_type": "campaign", "target_id": "22501517186",
         "target_name": "PMax BuzzLead Pro (Venda por Indicação)",
         "params": {"daily_brl": 200},
         "verify_after_min": 60 * 24 * 5, "verify_metric": "cost_24h_min",
         "verify_threshold": 180, "on_success": "blz-pmax-360",
         "note": "Plano R$18k: PMax 82→200, escala se gastar ≥180/dia"},

        {"id": "blz-pmax-360", "channel": "gads", "action": "set_budget",
         "target_type": "campaign", "target_id": "22501517186",
         "target_name": "PMax BuzzLead Pro (Venda por Indicação)",
         "params": {"daily_brl": 360},
         "scheduled_for": in_5d.isoformat(),
         "note": "Escala condicional disparada por blz-pmax-200 verify"},

        # Search: 23 → 75
        {"id": "blz-search-75", "channel": "gads", "action": "set_budget",
         "target_type": "campaign", "target_id": "22171174479",
         "target_name": "Search BuzzLead Pro F1→F3",
         "params": {"daily_brl": 75},
         "verify_after_min": 60 * 24 * 7, "verify_metric": "cost_24h_min",
         "verify_threshold": 60,
         "note": "Plano R$18k: Search 22→75 (CPA atual R$229)"},

        # Smart: pausar (725 conv-fake / 0 deal real em 30d)
        {"id": "blz-smart-pause", "channel": "gads", "action": "pause",
         "target_type": "campaign", "target_id": "23110530892",
         "target_name": "Smart BuzzLead",
         "note": "Plano R$18k: Smart=0 deals reais → pause"},
    ]

    # Marca Meta como aviso (sem token Marketing API)
    meta_warn = {
        "ok": True,
        "meta_pending": "META_ACCESS_TOKEN não configurado. Ops Meta devem ser "
                        "aplicadas manualmente ou via /api/ops após configurar token.",
        "meta_summary": [
            "PAUSE: 6× conjuntos KLT/Lookalike sem volume",
            "BZL099 Leads180D: manter R$60/dia (vencedor)",
            "Demais conjuntos: ajuste fino com piso R$6/dia",
        ],
    }

    created, skipped = [], []
    for op in plan:
        existing = store.get_op(op["id"])
        if existing:
            skipped.append(op["id"]); continue
        sched = _parse_dt(op.get("scheduled_for"))
        store.enqueue(
            op_id=op["id"],
            channel=op["channel"], action=op["action"],
            target_type=op["target_type"], target_id=op.get("target_id"),
            target_name=op["target_name"], params=op.get("params") or {},
            scheduled_for=sched,
            verify_after_min=op.get("verify_after_min"),
            verify_metric=op.get("verify_metric"),
            verify_threshold=op.get("verify_threshold"),
            on_success=op.get("on_success"),
            note=op.get("note"),
        )
        created.append(op["id"])

    return jsonify({"ok": True, "created": created, "skipped": skipped, "meta": meta_warn})
