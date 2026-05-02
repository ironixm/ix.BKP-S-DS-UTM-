# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Main – V1.0.0                                  │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 16:23         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ main.py                                        │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

# main.py
import json
import os
import time
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request, render_template

from dealscore.deal_score import (
    FIELD_IDS,
    build_dealscore_payload,
    compute_deal_score,
)
from logger import log_event
from mappings import (
    DEAL_ANUNCIO_ISOLADO,
    DEAL_CAMPANHA_ISOLADA,
    DEAL_CAMPANHA_KEY,
    DEAL_CANAL_KEY,
    DEAL_CONJUNTO_ISOLADO,
    DEAL_CONTEUDO_KEY,
    DEAL_FONTE_KEY,
    DEAL_PUBLICO_ISOLADO,
    PERSON_ANUNCIO_ISOLADO,
    PERSON_CAMPANHA_ISOLADA,
    PERSON_CAMPANHA_KEY,
    PERSON_CANAL_KEY,
    PERSON_CONJUNTO_ISOLADO,
    PERSON_CONTEUDO_KEY,
    PERSON_FONTE_KEY,
    PERSON_PUBLICO_ISOLADO,
)
from parsers import parse_meta_campaign
from pd_api import (
    _request,
    get_deal,
    get_deals,
    get_deals_by_filter,
    get_deals_count_by_filter,
    get_deal_notes,
    get_organization,
    get_person,
    add_note,
    dedup_auto_notes_for_deal,
    update_deal,
    update_note,
    update_organization,
    update_person,
)
from notes_builder import (
    build_auto_section,
    compose_full_note,
    extract_manual_section,
    extract_previous_entries,
    generate_alerts,
    _is_auto_note,
)
from product_match import assign_product_to_deal
from ltv import build_ltv_payload
from conversions import fire_funnel_event, detect_triggers

app = Flask(__name__)

# Init Postgres (best-effort, antes de tudo)
try:
    from modules import db as _db
    if _db.is_enabled():
        _db.init_schema()
        print(f"[main] Postgres OK (schema ready)", flush=True)
    else:
        print("[main] DATABASE_URL ausente — usando arquivos locais", flush=True)
except Exception as _e:
    print(f"⚠️  DB init falhou: {_e}", flush=True)

# Registrar blueprint do MadMode admin (com flask-login)
try:
    from modules.admin import register as register_madmode, start_scheduler
    register_madmode(app)
    start_scheduler()
except Exception as _e:
    import traceback
    print(f"⚠️  MadMode admin não inicializou: {_e}")
    traceback.print_exc()

# Registrar módulo ad_ops (operações de mídia agendadas)
try:
    from modules.ad_ops import ad_ops_bp, start_ad_ops_scheduler, init_db as _ad_ops_init
    _ad_ops_init()
    app.register_blueprint(ad_ops_bp)
    start_ad_ops_scheduler()
    print("[main] ad_ops registrado", flush=True)
except Exception as _e:
    import traceback
    print(f"⚠️  ad_ops não inicializou: {_e}")
    traceback.print_exc()

# =====================================================
from dealscore.deal_score_rules import (
    score_to_emoji,
    apply_emoji_prefix,
    ALL_TIER_EMOJIS,
)

# HEALTH CHECK (obrigatório pro deploy)
# =====================================================
@app.route("/")
def root():
    return jsonify({"status": "ok"}), 200


# =====================================================
# UI
# =====================================================
@app.route("/sync-ui")
def sync_ui():
    return render_template("sync_ui.html")


@app.route("/dates-ui")
def dates_ui():
    return render_template("dates_ui.html")


# =====================================================
# HELPERS
# =====================================================
def safe_deal_id(value):
    try:
        value = int(value)
        return value if value > 0 else None
    except Exception:
        return None


def _parse_iso(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_date_only(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _build_range(payload):
    mode = payload.get("range_mode")
    now = datetime.now(timezone.utc)
    start = end = None

    if mode == "last_days":
        days = int(payload.get("last_days") or 0)
        start = now - timedelta(days=days)
        end = now
    elif mode == "after_date":
        start = _parse_date_only(payload.get("after_date"))
    elif mode == "before_date":
        end = _parse_date_only(payload.get("before_date"))
    elif mode == "custom":
        start = _parse_date_only(payload.get("start_date"))
        end = _parse_date_only(payload.get("end_date"))

    return start, end


def _in_range(dt, start, end):
    if not dt:
        return False
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


# =====================================================
# CORE — PROCESSA 1 DEAL
# =====================================================
def process_deal(deal, mode="write", override=False):
    print("\n=== PROCESSANDO DEAL ===")
    print("DEAL ID:", deal.get("id"))

    person = deal.get("person_id") or {}
    person_id = person.get("value")

    if not person_id:
        print("⚠️ Deal sem person_id — ignorado")
        return None

    payload_person = {}
    payload_deal = {}

    # ---------- Cópia direta ----------
    fonte = deal.get(DEAL_FONTE_KEY)
    canal = deal.get(DEAL_CANAL_KEY)
    campanha = deal.get(DEAL_CAMPANHA_KEY)

    print("FONTE:", fonte)
    print("CANAL:", canal)
    print("CAMPANHA RAW:", campanha)

    if fonte:
        payload_person[PERSON_FONTE_KEY] = fonte

    if canal:
        payload_person[PERSON_CANAL_KEY] = canal

    if campanha:
        payload_person[PERSON_CAMPANHA_KEY] = campanha

    # ---------- Derivados ----------
    derivados = parse_meta_campaign(campanha)
    print("DERIVADOS:", derivados)

    for key, deal_field, person_field in [
        ("campanha_isolada", DEAL_CAMPANHA_ISOLADA, PERSON_CAMPANHA_ISOLADA),
        ("conjunto_isolado", DEAL_CONJUNTO_ISOLADO, PERSON_CONJUNTO_ISOLADO),
        ("publico_isolado", DEAL_PUBLICO_ISOLADO, PERSON_PUBLICO_ISOLADO),
        ("anuncio_isolado", DEAL_ANUNCIO_ISOLADO, PERSON_ANUNCIO_ISOLADO),
    ]:
        value = derivados.get(key)
        if value:
            if override or not deal.get(deal_field):
                payload_deal[deal_field] = value
            payload_person[person_field] = value

    anuncio = derivados.get("anuncio_isolado")
    if anuncio and (override or not deal.get(DEAL_CONTEUDO_KEY)):
        payload_deal[DEAL_CONTEUDO_KEY] = anuncio
        payload_person[PERSON_CONTEUDO_KEY] = anuncio

    print("PAYLOAD PERSON:", payload_person)
    print("PAYLOAD DEAL:", payload_deal)

    # ---------- Escrita UTM ----------
    if mode == "write":
        if payload_person:
            update_person(person_id, payload_person)
        if payload_deal:
            update_deal(deal["id"], payload_deal)

    # ---------- DEAL SCORE (SEMPRE EXECUTA) ----------
    score = None
    try:
        print("📊 Calculando DealScore...")

        person_full = get_person(person_id)

        score = compute_deal_score(
            deal=deal,
            person=person_full,
            field_ids=FIELD_IDS,
        )

        log_event(
            "deal_score",
            {
                "source": "sync" if request.endpoint == "sync" else "webhook",
                "deal_id": deal["id"],
                "person_id": person_id,
                "stage_id": deal.get("stage_id"),
                "score": score.total,
                "parts": score.parts,
            },
        )

        if mode == "write":
            update_deal(
                deal["id"],
                build_dealscore_payload(score.total),
            )
            # --- Emoji prefix no título ---
            old_title = deal.get("title") or ""
            new_title = apply_emoji_prefix(old_title, score.total)
            if new_title != old_title:
                update_deal(deal["id"], {"title": new_title})
                deal["title"] = new_title
                print(f"🏷️ Título: '{old_title}' → '{new_title}'")

            # --- Rich Notes (com lock por deal_id para evitar race entre workers) ---
            _skip_note_write = False
            try:
                from modules.locks import deal_lock
                with deal_lock(deal["id"]):
                    # Guard cross-worker: se outra réplica acabou de gerar a nota deste deal
                    # nos últimos 20s, pula reescrita pra não criar duplicata em rajada.
                    try:
                        import time as _t
                        from modules import db as _db
                        _gkey = f"note_lock:{deal['id']}"
                        _last = _db.state_get(_gkey) or {}
                        _now_ms = int(_t.time() * 1000)
                        _age = (_now_ms - int(_last.get("ts_ms", 0))) / 1000.0
                        if 0 < _age < 20:
                            print(f"🛡️  note_lock HIT deal={deal['id']} age={_age:.1f}s — skip note write")
                            _skip_note_write = True
                        else:
                            _db.state_set(_gkey, {"ts_ms": _now_ms})
                    except Exception as _ge:
                        print(f"⚠️ note_lock guard falhou (continuando): {_ge}")

                    if not _skip_note_write:
                        # Pré-dedup: se já existem duplicatas (legado), limpa antes de mexer
                        try:
                            dedup_auto_notes_for_deal(deal["id"])
                        except Exception as _e:
                            print(f"⚠️ pré-dedup falhou: {_e}")

                        notes = get_deal_notes(deal["id"])
                        auto_notes = [n for n in notes if _is_auto_note(n.get("content") or "")]
                        existing_note = auto_notes[0] if auto_notes else None

                        existing_html = (existing_note or {}).get("content", "")
                        manual = extract_manual_section(existing_html)
                        previous = extract_previous_entries(existing_html)
                        is_initial = existing_note is None

                        alertas = generate_alerts(score.total, score.parts, deal)

                        auto_html = build_auto_section(
                            score=score.total,
                            parts=score.parts,
                            fonte=deal.get(DEAL_FONTE_KEY),
                            canal=deal.get(DEAL_CANAL_KEY),
                            campanha=deal.get(DEAL_CAMPANHA_KEY),
                            anuncio=deal.get(DEAL_ANUNCIO_ISOLADO),
                            alertas=alertas,
                            previous_entries=previous,
                            is_initial=is_initial,
                        )

                        full_html = compose_full_note(manual, auto_html)

                        if existing_note:
                            update_note(existing_note["id"], full_html)
                            print(f"📝 Nota atualizada (id={existing_note['id']})")
                        else:
                            add_note(deal["id"], full_html)
                            print("📝 Nota criada")

                        # Pós-dedup: se algo escapou (ex.: race em outro worker), limpa
                        try:
                            dedup_auto_notes_for_deal(deal["id"])
                        except Exception as _e:
                            print(f"⚠️ pós-dedup falhou: {_e}")

            except Exception as e:
                print(f"⚠️ Erro ao gerar Rich Note: {e}")

            # --- Auto-product assignment ---
            try:
                product_result = assign_product_to_deal(deal["id"], score.total)
                if product_result:
                    if product_result.get("assigned"):
                        print(f"📦 Produto vinculado: {product_result['setup']['tier']} + {product_result['mensalidade']['tier']}")
                    elif product_result.get("skipped"):
                        print(f"📦 Produto: {product_result['reason']}")
            except Exception as e:
                print(f"⚠️ Erro ao vincular produto: {e}")

            # --- LTV / Tenure / ConversionValue ---
            try:
                ltv_payload = build_ltv_payload(deal, score.total)
                if ltv_payload:
                    update_deal(deal["id"], ltv_payload)
                    ltv_val = ltv_payload.get("2f32fa11d07ec6558c006b367fae78f0a00f4e3f")
                    if ltv_val:
                        print(f"💰 LTV=R${ltv_val:,.0f} (tenure={ltv_payload.get('fd6bd8ab463dfe1834bba1145e1607cd00e0cc3f', 'mantido')}m)")
                    else:
                        print("💰 LTV: mantido (já definido)")
            except Exception as e:
                print(f"⚠️ Erro ao calcular LTV: {e}")

    except Exception as e:
        print("❌ ERRO AO CALCULAR DEAL SCORE:", str(e))

    return {
        "deal_id": deal["id"],
        "deal_title": deal.get("title"),
        "deal_url": f"https://web.agendor.com.br/deal/{deal['id']}",
        "person_id": person_id,
        "deal_payload": payload_deal,
        "person_payload": payload_person,
        "deal_score": score.total if score else None,
    }


# =====================================================
# BACKFILL / MANUAL
# =====================================================
@app.route("/sync/count")
def sync_count():
    filter_id = request.args.get("filter_id", type=int)
    if not filter_id:
        return jsonify({"error": "filter_id obrigatório"}), 400

    total = get_deals_count_by_filter(filter_id)

    return jsonify({
        "filter_id": filter_id,
        "total": total,
    })


@app.route("/sync/")
def sync():
    filter_id = request.args.get("filter_id", type=int)
    if not filter_id:
        return jsonify({"error": "filter_id obrigatório"}), 400

    start = request.args.get("start", 0, type=int)
    limit = request.args.get("limit", 100, type=int)
    mode = request.args.get("mode", "test")
    override = request.args.get("override", "0") == "1"

    print(
        f"\n=== SYNC START === filter={filter_id} start={start} limit={limit}")

    resp = get_deals_by_filter(filter_id, start=start, limit=limit)

    deals = resp["data"]
    pagination = resp["pagination"]

    # 🔴 REGRA DE OURO
    if not deals:
        return jsonify({
            "status": "ok",
            "filter_id": filter_id,
            "start": start,
            "limit": limit,
            "processed": 0,
            "results": [],
            "pagination": {
                "more_items_in_collection": False
            }
        })

    results = []
    for stub in deals:
        deal_id = stub.get("id") or stub.get("deal_id")
        if not deal_id:
            continue

        deal = get_deal(deal_id)
        if not deal:
            continue

        r = process_deal(deal, mode=mode, override=override)
        if r:
            results.append(r)

    print(f"=== SYNC END === processados={len(results)}")

    return jsonify({
        "status": "ok",
        "filter_id": filter_id,
        "start": start,
        "limit": limit,
        "processed": len(results),
        "results": results,
        "pagination": pagination,
    })


# =====================================================
# DATA FIXER — PREVIEW / NORMALIZE
# =====================================================


@app.route("/dates/preview", methods=["POST"])
def dates_preview():
    payload = request.get_json(silent=True) or {}
    range_mode = payload.get("range_mode")
    date_field = payload.get("date_field")
    if range_mode not in {"last_days", "after_date", "before_date", "custom"}:
        return jsonify({"error": "range_mode invalido"}), 400
    if date_field not in {"person_created", "org_created", "deal_created"}:
        return jsonify({"error": "date_field invalido"}), 400

    start_dt, end_dt = _build_range(payload)
    if range_mode in {"after_date", "custom"} and not start_dt:
        return jsonify({"error": "start_date/after_date obrigatorio"}), 400
    if range_mode in {"before_date", "custom"} and not end_dt:
        return jsonify({"error": "end_date/before_date obrigatorio"}), 400

    results = []
    scanned = 0
    limit = 100
    start = 0
    max_scan = int(payload.get("max_scan") or 2000)
    truncated = False

    person_cache = {}
    org_cache = {}

    while True:
        resp = get_deals(start=start, limit=limit, status="all_not_deleted", sort="add_time DESC")
        deals = resp["data"]
        if not deals:
            break

        for deal in deals:
            if scanned >= max_scan:
                truncated = True
                break

            scanned += 1

            deal_add_time = _parse_iso(deal.get("add_time"))
            if date_field == "deal_created":
                match_dt = deal_add_time
            else:
                match_dt = None

            person_id = None
            person_name = None
            person_add_time = None
            person = deal.get("person_id") or {}
            person_id = person.get("value") if isinstance(person, dict) else person

            if person_id:
                if person_id not in person_cache:
                    person_cache[person_id] = get_person(person_id) or {}
                person_data = person_cache[person_id]
                person_name = person_data.get("name")
                person_add_time = _parse_iso(person_data.get("add_time"))
                if date_field == "person_created":
                    match_dt = person_add_time

            org_id = deal.get("org_id")
            org_name = None
            org_add_time = None
            if isinstance(org_id, dict):
                org_id = org_id.get("value")
            if org_id:
                if org_id not in org_cache:
                    org_cache[org_id] = get_organization(org_id) or {}
                org_data = org_cache[org_id]
                org_name = org_data.get("name")
                org_add_time = _parse_iso(org_data.get("add_time"))
                if date_field == "org_created":
                    match_dt = org_add_time

            if _in_range(match_dt, start_dt, end_dt):
                results.append({
                    "deal_id": deal.get("id"),
                    "deal_title": deal.get("title"),
                    "deal_add_time": deal_add_time.isoformat() if deal_add_time else None,
                    "person_id": person_id,
                    "person_name": person_name,
                    "person_add_time": person_add_time.isoformat() if person_add_time else None,
                    "org_id": org_id,
                    "org_name": org_name,
                    "org_add_time": org_add_time.isoformat() if org_add_time else None,
                })

            if date_field == "deal_created" and start_dt and deal_add_time and deal_add_time < start_dt:
                truncated = False
                deals = []
                break

        if truncated or not deals:
            break

        start += limit

    return jsonify({
        "status": "ok",
        "rows": results,
        "scanned": scanned,
        "truncated": truncated,
    })


@app.route("/dates/normalize", methods=["POST"])
def dates_normalize():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "rows obrigatorio"}), 400

    results = []
    for row in rows:
        deal_id = row.get("deal_id")
        person_id = row.get("person_id")
        org_id = row.get("org_id")
        target_date = row.get("target_date")
        if not target_date:
            results.append({
                "deal_id": deal_id,
                "status": "skipped",
                "reason": "target_date ausente",
            })
            continue

        payload_date = {"add_time": target_date}
        row_result = {"deal_id": deal_id, "target_date": target_date}

        try:
            if deal_id:
                update_deal(deal_id, payload_date)
            row_result["deal"] = "ok"
        except Exception as exc:
            row_result["deal"] = f"erro: {exc}"

        try:
            if person_id:
                update_person(person_id, payload_date)
            row_result["person"] = "ok"
        except Exception as exc:
            row_result["person"] = f"erro: {exc}"

        try:
            if org_id:
                update_organization(org_id, payload_date)
            row_result["org"] = "ok"
        except Exception as exc:
            row_result["org"] = f"erro: {exc}"

        results.append(row_result)

    return jsonify({
        "status": "ok",
        "results": results,
    })


# =====================================================
# DIAGNÓSTICO — PRODUTOS PIPEDRIVE
# =====================================================
@app.route("/products/list")
def products_list():
    from product_match import list_available_products
    products = list_available_products()
    return jsonify({"products": products, "total": len(products)})


# =====================================================
# WEBHOOK PIPEDRIVE (COM DELAY DEFENSIVO)
# =====================================================
@app.route("/webhook/pipedrive/", methods=["POST"])
@app.route("/webhook/agendor/", methods=["POST"], defaults={"event_name": None})
@app.route("/webhook/agendor/<event_name>/", methods=["POST"])
@app.route("/webhook/agendor/<event_name>", methods=["POST"])
def webhook_pipedrive(event_name=None):
    payload = request.get_json(silent=True) or {}

    print(f"\n=== WEBHOOK RECEBIDO (event={event_name}) ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # 🔹 LOG IMEDIATO (antes de qualquer normalização) para health check
    # e para inspecionar o formato real do Agendor.
    try:
        log_event("webhook_received", {
            "source": "agendor",
            "agendor_event": event_name,
            "raw_payload": payload,
        })
    except Exception as _le:
        print(f"[webhook] log_event FAIL: {_le}", flush=True)

    # ───────────────────────────────────────────────────────────
    # Normaliza payload Agendor → formato v1.0 (event+current)
    # Agendor REAL envia: { "data": { id, dealStage:{id}, dealStatus:{id,name}, ... } }
    # SEM campo "event" — o tipo do webhook vem na URL (path).
    # Mapeamento: docs/agendor-bkp-eventos.md
    # ───────────────────────────────────────────────────────────
    if "data" in payload and "current" not in payload:
        data = payload.get("data") or {}
        # Achata dealStage/dealStatus para o formato esperado por detect_triggers/get_deal
        flat = dict(data)
        if isinstance(data.get("dealStage"), dict):
            flat["stage_id"] = data["dealStage"].get("id")
        if isinstance(data.get("dealStatus"), dict):
            ds_id = data["dealStatus"].get("id")
            # 1=ongoing, 2=won, 3=lost (mapping Agendor)
            flat["status"] = {1: "open", 2: "won", 3: "lost"}.get(ds_id, "open")
        # event_name vem do path: on_deal_created → action=create entity=deal
        ev = (event_name or "").lower()
        action_map = {
            "on_deal_created": ("create", "deal"),
            "on_deal_updated": ("update", "deal"),
            "on_deal_stage_updated": ("change_stage", "deal"),
            "on_deal_won": ("won", "deal"),
            "on_deal_lost": ("lost", "deal"),
            "on_deal_deleted": ("delete", "deal"),
            "on_person_created": ("create", "person"),
            "on_person_updated": ("update", "person"),
            "on_person_deleted": ("delete", "person"),
            "on_organization_created": ("create", "organization"),
            "on_organization_updated": ("update", "organization"),
            "on_organization_deleted": ("delete", "organization"),
            "on_activity_created": ("create", "activity"),
        }
        action, entity = action_map.get(ev, ("update", "deal"))
        payload = {
            "event": f"{action}.{entity}",
            "current": flat,
            "previous": {},
            "meta": {
                "action": action, "entity": entity,
                "source": "agendor", "agendor_event": ev,
            },
        }

    # Compat legado v2.0 (meta+data)
    if "meta" in payload and "data" in payload and "current" not in payload:
        meta = payload.get("meta") or {}
        payload = {
            "event": f"{meta.get('action')}.{meta.get('entity')}",
            "current": payload.get("data") or {},
            "previous": payload.get("previous") or {},
            "meta": meta,
        }

    raw_id = None

    if isinstance(payload.get("current"), dict):
        raw_id = payload["current"].get("id")

    if not raw_id and isinstance(payload.get("previous"), dict):
        raw_id = payload["previous"].get("id")

    # ───────────────────────────────────────────────────────────
    # ENRICHMENT: webhooks de org/person disparam pipeline async
    # (não passam pelo fluxo de deal/conversões).
    # ───────────────────────────────────────────────────────────
    meta = payload.get("meta") or {}
    entity = meta.get("entity")
    if entity in ("organization", "person") and raw_id:
        try:
            import threading
            from enrichment import enrich_organization, enrich_person
            target = enrich_organization if entity == "organization" else enrich_person
            t = threading.Thread(target=target, args=(raw_id,),
                                 kwargs={"mode": "auto"}, daemon=True)
            t.start()
            return jsonify({
                "status": "enrichment_queued",
                "entity": entity, "entity_id": raw_id,
            }), 200
        except Exception as _e:
            print(f"[enrichment] dispatch FAIL: {_e}", flush=True)
            return jsonify({"status": "enrichment_error",
                            "error": str(_e)}), 200

    deal_id = safe_deal_id(raw_id)

    if not deal_id:
        print("⚠️ Webhook ignorado — ID inválido:", raw_id)
        return jsonify({
            "status": "ignored",
            "reason": "invalid_or_non_numeric_deal_id",
            "raw_id": raw_id,
        }), 200

    # 🛡️ DEDUP DE WEBHOOKS (Pipedrive reenvia em rajada quando vários campos
    # são alterados quase simultaneamente). Janela: 30s por (deal_id, action).
    # Usa singleton_state no Postgres p/ funcionar entre múltiplos workers.
    try:
        from modules import db as _db
        if _db.is_enabled():
            action = (
                (payload.get("meta") or {}).get("action")
                or (payload.get("event") or "").split(".")[0]
                or "any"
            )
            dedup_key = f"webhook_dedup:{deal_id}:{action}"
            now_ms = int(time.time() * 1000)
            last = _db.state_get(dedup_key) or {}
            last_ms = int(last.get("ts_ms", 0))
            if now_ms - last_ms < 30_000:
                age = (now_ms - last_ms) / 1000
                print(f"🛡️  Webhook dedup HIT deal={deal_id} action={action} age={age:.1f}s — ignorado")
                return jsonify({
                    "status": "deduped",
                    "deal_id": deal_id,
                    "last_seen_seconds_ago": age,
                }), 200
            _db.state_set(dedup_key, {"ts_ms": now_ms, "action": action})
    except Exception as _e:
        print(f"[webhook] dedup check FAIL (continuando): {_e}")

    # ⏳ DELAY DEFENSIVO (CRÍTICO)
    print("⏳ Aguardando 2s para consistência do Pipedrive...")
    time.sleep(2)

    deal = get_deal(deal_id)
    if not deal:
        print("⚠️ Deal não encontrado após delay:", deal_id)
        return jsonify({
            "status": "not_found",
            "deal_id": deal_id,
        }), 200

    # ── Disparo de eventos de funil (Meta CAPI + GA4 + GAds) ──
    conv_triggers = detect_triggers(payload)
    conv_results = {}
    if conv_triggers:
        person_ref = deal.get("person_id") or {}
        person_id = person_ref.get("value") if isinstance(person_ref, dict) else person_ref
        person_full = get_person(person_id) if person_id else None
        ltv_value = float(deal.get("value") or 0)
        for trigger in conv_triggers:
            res = fire_funnel_event(
                trigger=trigger, deal=deal, person=person_full,
                value=ltv_value if trigger == "status_won" else 0.0,
            )
            conv_results[trigger] = res
            try:
                from logger import log_event as _log_ev
                from conversions import STAGE_EVENT_MAP, WON_EVENTS, LOST_EVENTS
                if trigger.startswith("stage_"):
                    cfg = STAGE_EVENT_MAP.get(int(trigger.split("_")[1])) or {}
                elif trigger == "status_won":
                    cfg = WON_EVENTS
                elif trigger == "status_lost":
                    cfg = LOST_EVENTS
                else:
                    cfg = {}
                for plat in ("meta", "ga4", "gads"):
                    pres = (res or {}).get(plat)
                    if pres is None:
                        continue
                    ev_name = cfg.get(plat)
                    if isinstance(ev_name, tuple):
                        ev_name = ev_name[0]
                    _log_ev("conversion_sent", {
                        "platform": plat,
                        "event_name": ev_name,
                        "trigger": trigger,
                        "deal_id": deal_id,
                        "value": ltv_value if trigger == "status_won" else 0.0,
                        "ok": bool((pres or {}).get("ok")),
                        "status": (pres or {}).get("status"),
                        "reason": (pres or {}).get("reason"),
                        "error": (pres or {}).get("error"),
                    })
            except Exception as _le:
                pass

    result = process_deal(deal, mode="write", override=False)

    return jsonify({
        "status": "ok",
        "deal_id": deal_id,
        "result": result,
        "conversions": conv_results,
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

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
