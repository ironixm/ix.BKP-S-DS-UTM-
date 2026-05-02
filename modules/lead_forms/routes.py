"""Blueprints HTTP para Lead Forms (Meta + GAds).

Rotas públicas (webhooks):
  GET  /webhook/meta/leadgen   — verificação (hub.challenge)
  POST /webhook/meta/leadgen   — notificação de novo lead
  POST /webhook/gads/leadform  — Google Ads Lead Form Extension push

Rotas admin (autenticadas):
  GET  /madmode/api/lead-forms/stats
  GET  /madmode/api/lead-forms/recent?provider=meta&limit=50
  GET  /madmode/api/meta/forms                    — lista forms da página
  POST /madmode/api/meta/backfill                 — body {form_id, since?, dry_run?}
  POST /madmode/api/lead-forms/replay             — body {provider, lead_id}
"""
from __future__ import annotations
import os
import json
import time
import hmac
import hashlib

from flask import Blueprint, request, jsonify, abort

from . import store, mapper, pusher, meta_client


# ─── Blueprint público (webhooks) ─────────────────────────────
public_bp = Blueprint("lead_forms_public", __name__)


@public_bp.route("/webhook/meta/leadgen", methods=["GET"])
def meta_verify():
    """Verificação de webhook do Meta (hub.challenge)."""
    expected = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token and token == expected:
        return challenge or "", 200
    return "forbidden", 403


def _verify_meta_signature(raw_body: bytes, header_sig: str | None) -> bool:
    secret = os.environ.get("META_APP_SECRET", "")
    if not secret or not header_sig:
        # Sem app_secret configurado, aceita (modo permissivo). Loga warning.
        return True
    try:
        algo, sig = header_sig.split("=", 1)
        if algo != "sha256":
            return False
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False


@public_bp.route("/webhook/meta/leadgen", methods=["POST"])
def meta_webhook():
    """Recebe notificação leadgen, busca lead via Graph, push pro Agendor."""
    raw = request.get_data() or b""
    sig = request.headers.get("X-Hub-Signature-256")
    if not _verify_meta_signature(raw, sig):
        return jsonify({"error": "invalid signature"}), 401
    payload = request.get_json(silent=True) or {}
    results = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "leadgen":
                continue
            v = change.get("value") or {}
            lead_id = v.get("leadgen_id")
            form_id = v.get("form_id")
            if not lead_id:
                continue
            # Busca dados completos do lead
            r = meta_client.get_lead(str(lead_id))
            if not r.get("ok"):
                store.record("meta", str(lead_id), form_id=str(form_id) if form_id else None,
                             status="error", error=f"fetch: {r.get('error')}",
                             payload={"webhook_value": v})
                results.append({"lead_id": lead_id, "ok": False, "error": "fetch_failed"})
                continue
            norm = mapper.from_meta_lead(r["data"])
            res = pusher.push_to_agendor(norm, "meta")
            results.append({"lead_id": lead_id, **res})
    return jsonify({"received": len(results), "results": results})


@public_bp.route("/webhook/gads/leadform", methods=["POST"])
def gads_webhook():
    """Recebe push do Google Ads Lead Form Extension.

    Validação por chave compartilhada (campo configurável "key" na URL ou
    header 'X-Lead-Webhook-Key'), comparado com env GADS_WEBHOOK_KEY.
    """
    expected = os.environ.get("GADS_WEBHOOK_KEY", "")
    sent = (request.args.get("key")
            or request.headers.get("X-Lead-Webhook-Key")
            or (request.get_json(silent=True) or {}).get("google_key"))
    if expected and sent != expected:
        return jsonify({"error": "invalid key"}), 401
    payload = request.get_json(silent=True) or {}
    norm = mapper.from_gads_lead(payload)
    if not norm.get("lead_id"):
        # GAds às vezes não envia lead_id — gera um determinístico
        norm["lead_id"] = hashlib.sha1(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        norm["external_id"] = f"gads:{norm.get('source_meta',{}).get('form_id','')}:{norm['lead_id']}"
    res = pusher.push_to_agendor(norm, "gads")
    return jsonify(res), (200 if res.get("ok") else 500)


# ─── Blueprint admin (autenticado) ────────────────────────────
admin_bp = Blueprint("lead_forms_admin", __name__, url_prefix="/madmode/api")


def _require_admin():
    """Reaproveita auth do madmode."""
    try:
        from modules.admin.auth import require_admin as _ra
        return _ra
    except Exception:
        return lambda f: f


require_admin = _require_admin()


@admin_bp.route("/lead-forms/stats")
@require_admin
def lf_stats():
    return jsonify(store.stats())


@admin_bp.route("/lead-forms/recent")
@require_admin
def lf_recent():
    provider = request.args.get("provider")
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 500))
    except Exception:
        limit = 50
    return jsonify({"items": store.list_recent(limit=limit, provider=provider)})


@admin_bp.route("/meta/forms")
@require_admin
def meta_forms():
    page_id = request.args.get("page_id") or meta_client.get_page_id()
    pages = meta_client.list_pages()
    forms = meta_client.list_lead_forms(page_id) if page_id else {"ok": False, "error": "page_id"}
    return jsonify({"page_id": page_id, "pages": pages, "forms": forms})


@admin_bp.route("/meta/backfill", methods=["POST"])
@require_admin
def meta_backfill():
    body = request.get_json(silent=True) or {}
    form_id = str(body.get("form_id") or "").strip()
    if not form_id:
        return jsonify({"error": "form_id obrigatório"}), 400
    since = body.get("since")
    since_unix = None
    if since:
        try:
            since_unix = int(since)
        except (TypeError, ValueError):
            try:
                from datetime import datetime
                since_unix = int(datetime.fromisoformat(str(since).replace("Z","")).timestamp())
            except Exception:
                return jsonify({"error": "since inválido (use unix ou ISO)"}), 400
    dry = bool(body.get("dry_run"))
    max_pages = int(body.get("max_pages", 20))

    processed = []
    errors = 0
    for lead in meta_client.iter_all_leads(form_id, since_unix=since_unix, max_pages=max_pages):
        if "_error" in lead:
            return jsonify({"error": lead["_error"], "processed": processed}), 502
        norm = mapper.from_meta_lead(lead)
        if dry:
            processed.append({"lead_id": norm["lead_id"], "would_push": True,
                              "name": norm.get("name"), "email": norm.get("email")})
            continue
        res = pusher.push_to_agendor(norm, "meta")
        if not res.get("ok"):
            errors += 1
        processed.append({"lead_id": norm["lead_id"], **res})
    return jsonify({"form_id": form_id, "since": since_unix, "dry_run": dry,
                    "count": len(processed), "errors": errors, "results": processed})


@admin_bp.route("/lead-forms/replay", methods=["POST"])
@require_admin
def lf_replay():
    """Tenta reprocessar 1 lead que falhou."""
    body = request.get_json(silent=True) or {}
    provider = (body.get("provider") or "").strip()
    lead_id  = str(body.get("lead_id") or "").strip()
    if not provider or not lead_id:
        return jsonify({"error": "provider e lead_id obrigatórios"}), 400
    if provider == "meta":
        r = meta_client.get_lead(lead_id)
        if not r.get("ok"):
            return jsonify({"error": "fetch_failed", "detail": r}), 502
        norm = mapper.from_meta_lead(r["data"])
        # Força reprocesso ignorando dedup
        store.record(provider, lead_id, status="pending", payload=norm)
        from . import store as _s
        with _s._conn() as c:
            c.execute("DELETE FROM leadform_ingested WHERE provider=? AND lead_id=?",
                      (provider, lead_id))
        return jsonify(pusher.push_to_agendor(norm, "meta"))
    return jsonify({"error": "replay só implementado para meta no momento"}), 400
