"""Camada de acesso ao Postgres.

- Lê DATABASE_URL do env. Se ausente, retorna None nos getters → caller faz fallback p/ JSON/log file.
- ConnectionPool global, lazy init.
- Schema criado idempotente em init_schema() (chamado no startup do app).
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

_pool = None
_pool_lock = threading.Lock()
_schema_ready = False


def database_url() -> Optional[str]:
    url = os.environ.get("DATABASE_URL", "").strip()
    return url or None


def is_enabled() -> bool:
    return bool(database_url())


def _get_pool():
    """Lazy init do pool (psycopg3)."""
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:
            return _pool
        url = database_url()
        if not url:
            return None
        try:
            from psycopg_pool import ConnectionPool  # type: ignore
        except ImportError:
            return None
        # Normaliza esquema postgres:// → psycopg aceita
        _pool = ConnectionPool(url, min_size=1, max_size=4, timeout=10, kwargs={"autocommit": False})
        return _pool


@contextmanager
def conn_ctx() -> Iterator[Any]:
    """Yields uma conexão do pool. Lança RuntimeError se DB indisponível."""
    p = _get_pool()
    if p is None:
        raise RuntimeError("DATABASE_URL não configurada")
    with p.connection() as cn:
        yield cn


def init_schema() -> bool:
    """Cria as tabelas se não existirem. Retorna True se DB ok, False se sem DB."""
    global _schema_ready
    if _schema_ready:
        return True
    if not is_enabled():
        return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute(_SCHEMA_SQL)
            cn.commit()
        _schema_ready = True
        return True
    except Exception as e:  # noqa: BLE001
        # Race condition entre múltiplos workers gunicorn é benigna se as tabelas existem
        msg = str(e).lower()
        if "already exists" in msg or "duplicate key" in msg:
            _schema_ready = True
            return True
        print(f"[db] init_schema FAIL: {e}", flush=True)
        return False


_SCHEMA_SQL = """
-- Eventos do pipeline (substitui events.log)
CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type        TEXT NOT NULL,
    deal_id     BIGINT,
    person_id   BIGINT,
    org_id      BIGINT,
    stage_id    BIGINT,
    score       INTEGER,
    parts       JSONB,
    source      TEXT,
    payload     JSONB
);
CREATE INDEX IF NOT EXISTS idx_events_ts        ON events (ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_type_ts   ON events (type, ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_deal      ON events (deal_id, ts DESC);

-- Jobs do scheduler (substitui scheduler_jobs.json)
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id              TEXT PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          TEXT NOT NULL,
    batch_size      INTEGER NOT NULL,
    freq_minutes    INTEGER NOT NULL,
    date_from       DATE,
    date_to         DATE,
    date_field      TEXT,
    status_filter   TEXT,
    with_notes      BOOLEAN DEFAULT TRUE,
    with_prefill    BOOLEAN DEFAULT FALSE,
    with_dedup      BOOLEAN DEFAULT FALSE,
    sort_dir        TEXT DEFAULT 'DESC',
    cursor_start    INTEGER DEFAULT 0,
    processed       INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ,
    estimated_daily_tokens INTEGER,
    extra           JSONB
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_next ON scheduler_jobs (status, next_run_at);

-- Histórico de runs do dedup
CREATE TABLE IF NOT EXISTS dedup_runs (
    id              BIGSERIAL PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    deal_id         BIGINT,
    deals_scanned   INTEGER DEFAULT 0,
    notes_deleted   INTEGER DEFAULT 0,
    errors          INTEGER DEFAULT 0,
    status          TEXT
);

-- Estado do prefill async (1 linha global)
CREATE TABLE IF NOT EXISTS singleton_state (
    key             TEXT PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Migrações idempotentes (colunas adicionadas após criação)
ALTER TABLE scheduler_jobs ADD COLUMN IF NOT EXISTS sort_dir TEXT DEFAULT 'DESC';
"""


# ===== Helpers =====================================================

def _to_iso(ts: Any) -> str:
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat()
    return str(ts) if ts else ""


def insert_event(*, type: str, deal_id: int | None = None, person_id: int | None = None,
                 org_id: int | None = None, stage_id: int | None = None,
                 score: int | None = None, parts: dict | None = None,
                 source: str | None = None, payload: dict | None = None) -> bool:
    if not is_enabled():
        return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute(
                """INSERT INTO events (type, deal_id, person_id, org_id, stage_id, score, parts, source, payload)
                   VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb)""",
                (type, deal_id, person_id, org_id, stage_id, score,
                 json.dumps(parts) if parts is not None else None,
                 source,
                 json.dumps(payload) if payload is not None else None),
            )
            cn.commit()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[db] insert_event FAIL: {e}", flush=True)
        return False


def fetch_events(limit: int = 50, type_filter: str | None = None,
                 since_iso: str | None = None) -> list[dict]:
    if not is_enabled():
        return []
    sql = "SELECT ts, type, deal_id, person_id, stage_id, score, parts, source, payload FROM events"
    where, params = [], []
    if type_filter:
        where.append("type = %s"); params.append(type_filter)
    if since_iso:
        where.append("ts >= %s"); params.append(since_iso)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ts DESC LIMIT %s"
    params.append(limit)
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c.name for c in cur.description]
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(zip(cols, r))
                d["timestamp"] = _to_iso(d.pop("ts"))
                out.append(d)
            return out
    except Exception as e:  # noqa: BLE001
        print(f"[db] fetch_events FAIL: {e}", flush=True)
        return []


def count_events(*, type_filter: str | None = None, since_iso: str | None = None) -> int:
    if not is_enabled():
        return 0
    sql = "SELECT COUNT(*) FROM events"
    where, params = [], []
    if type_filter:
        where.append("type = %s"); params.append(type_filter)
    if since_iso:
        where.append("ts >= %s"); params.append(since_iso)
    if where:
        sql += " WHERE " + " AND ".join(where)
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute(sql, params)
            return int(cur.fetchone()[0])
    except Exception:
        return 0


def aggregate_events_by_day(days: int = 14) -> list[dict]:
    if not is_enabled():
        return []
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                SELECT DATE_TRUNC('day', ts AT TIME ZONE 'America/Sao_Paulo')::date AS d,
                       type,
                       COUNT(*) AS n
                FROM events
                WHERE ts >= NOW() - (%s || ' days')::interval
                GROUP BY 1, 2
                ORDER BY 1
            """, (days,))
            return [{"day": str(r[0]), "type": r[1], "count": int(r[2])} for r in cur.fetchall()]
    except Exception as e:  # noqa: BLE001
        print(f"[db] aggregate FAIL: {e}", flush=True)
        return []


def overview_24h() -> dict:
    if not is_enabled():
        return {}
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE type='deal_score') AS deals,
                       AVG(score) FILTER (WHERE type='deal_score') AS avg_score,
                       COUNT(DISTINCT deal_id) FILTER (WHERE type='deal_score') AS unique_deals,
                       COUNT(*) FILTER (WHERE type LIKE 'conv_%%') AS conversions
                FROM events
                WHERE ts >= NOW() - interval '24 hours'
            """)
            r = cur.fetchone()
            return {
                "deals_24h": int(r[0] or 0),
                "avg_score_24h": float(r[1]) if r[1] is not None else None,
                "unique_deals_24h": int(r[2] or 0),
                "conversions_24h": int(r[3] or 0),
            }
    except Exception:
        return {}


def recent_deals(limit: int = 20) -> list[dict]:
    """Últimos deals atualizados (1 linha por deal_id)."""
    if not is_enabled():
        return []
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (deal_id)
                       deal_id, ts, score, parts, stage_id, source
                FROM events
                WHERE type = 'deal_score' AND deal_id IS NOT NULL
                ORDER BY deal_id, ts DESC
                LIMIT %s
            """, (limit,))
            cols = [c.name for c in cur.description]
            rows = cur.fetchall()
            out = []
            for r in rows:
                d = dict(zip(cols, r))
                d["timestamp"] = _to_iso(d.pop("ts"))
                out.append(d)
            out.sort(key=lambda x: x["timestamp"], reverse=True)
            return out
    except Exception:
        return []


# ===== Scheduler jobs ===============================================

def jobs_load_all() -> Optional[list[dict]]:
    """None se DB não disponível (caller usa fallback JSON)."""
    if not is_enabled():
        return None
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                SELECT id, status, batch_size, freq_minutes, date_from, date_to,
                       date_field, status_filter, with_notes, with_prefill, with_dedup,
                       sort_dir,
                       cursor_start, processed, errors, last_run_at, next_run_at,
                       estimated_daily_tokens, created_at, extra
                FROM scheduler_jobs
                ORDER BY created_at DESC
            """)
            cols = [c.name for c in cur.description]
            return [_row_to_job(dict(zip(cols, r))) for r in cur.fetchall()]
    except Exception as e:  # noqa: BLE001
        print(f"[db] jobs_load_all FAIL: {e}", flush=True)
        return None


def _row_to_job(r: dict) -> dict:
    return {
        "id": r["id"],
        "status": r["status"],
        "batch_size": r["batch_size"],
        "freq_minutes": r["freq_minutes"],
        "date_from": str(r["date_from"]) if r.get("date_from") else "",
        "date_to": str(r["date_to"]) if r.get("date_to") else "",
        "date_field": r["date_field"],
        "status_filter": r.get("status_filter"),
        "with_notes": bool(r.get("with_notes")),
        "with_prefill": bool(r.get("with_prefill")),
        "with_dedup": bool(r.get("with_dedup")),
        "sort_dir": (r.get("sort_dir") or "DESC"),
        "cursor_start": int(r.get("cursor_start") or 0),
        "processed": int(r.get("processed") or 0),
        "errors": int(r.get("errors") or 0),
        "last_run_at": _to_iso(r.get("last_run_at")) or None,
        "next_run_at": _to_iso(r.get("next_run_at")) or None,
        "estimated_daily_tokens": r.get("estimated_daily_tokens"),
        "created_at": _to_iso(r.get("created_at")),
    }


def jobs_save_all(jobs: list[dict]) -> bool:
    """Sincroniza a tabela com a lista (upsert + delete extras)."""
    if not is_enabled():
        return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            ids = [j["id"] for j in jobs]
            for j in jobs:
                cur.execute("""
                    INSERT INTO scheduler_jobs (id, status, batch_size, freq_minutes, date_from, date_to,
                        date_field, status_filter, with_notes, with_prefill, with_dedup, sort_dir,
                        cursor_start, processed, errors, last_run_at, next_run_at,
                        estimated_daily_tokens, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,NULLIF(%s,'')::date,NULLIF(%s,'')::date,
                            %s,%s,%s,%s,%s,%s,
                            %s,%s,%s,
                            NULLIF(%s,'')::timestamptz, NULLIF(%s,'')::timestamptz,
                            %s, NULLIF(%s,'')::timestamptz, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        status=EXCLUDED.status,
                        cursor_start=EXCLUDED.cursor_start,
                        processed=EXCLUDED.processed,
                        errors=EXCLUDED.errors,
                        last_run_at=EXCLUDED.last_run_at,
                        next_run_at=EXCLUDED.next_run_at,
                        sort_dir=EXCLUDED.sort_dir,
                        updated_at=NOW()
                """, (
                    j["id"], j["status"], j["batch_size"], j["freq_minutes"],
                    j.get("date_from") or "", j.get("date_to") or "",
                    j.get("date_field"), j.get("status_filter"),
                    bool(j.get("with_notes")), bool(j.get("with_prefill")), bool(j.get("with_dedup")),
                    (j.get("sort_dir") or "DESC"),
                    int(j.get("cursor_start") or 0),
                    int(j.get("processed") or 0),
                    int(j.get("errors") or 0),
                    j.get("last_run_at") or "", j.get("next_run_at") or "",
                    j.get("estimated_daily_tokens"), j.get("created_at") or "",
                ))
            if ids:
                cur.execute("DELETE FROM scheduler_jobs WHERE id <> ALL(%s)", (ids,))
            else:
                cur.execute("DELETE FROM scheduler_jobs")
            cn.commit()
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[db] jobs_save_all FAIL: {e}", flush=True)
        return False


# ===== Singleton state =============================================

def state_get(key: str) -> Any:
    if not is_enabled():
        return None
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("SELECT value FROM singleton_state WHERE key=%s", (key,))
            r = cur.fetchone()
            return r[0] if r else None
    except Exception:
        return None


def record_dedup_run(*, deal_id: int | None, deals_scanned: int = 1,
                     notes_deleted: int = 0, errors: int = 0,
                     status: str = "ok") -> bool:
    """Registra uma execução de dedup (usada para o card de índice de duplicação)."""
    if not is_enabled():
        return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                INSERT INTO dedup_runs (started_at, finished_at, deal_id,
                                        deals_scanned, notes_deleted, errors, status)
                VALUES (NOW(), NOW(), %s, %s, %s, %s, %s)
            """, (deal_id, deals_scanned, notes_deleted, errors, status))
            cn.commit()
        return True
    except Exception:
        return False


def dedup_stats(days: int = 7) -> dict:
    """Estatísticas dos últimos N dias para o card do dashboard."""
    if not is_enabled():
        return {"deals_scanned": 0, "notes_deleted": 0, "errors": 0,
                "runs": 0, "duplicate_rate": 0.0, "days": days}
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(deals_scanned),0),
                       COALESCE(SUM(notes_deleted),0),
                       COALESCE(SUM(errors),0),
                       COUNT(*)
                FROM dedup_runs
                WHERE started_at > NOW() - (%s || ' days')::interval
            """, (str(days),))
            r = cur.fetchone() or (0, 0, 0, 0)
        scanned, deleted, errors, runs = int(r[0]), int(r[1]), int(r[2]), int(r[3])
        rate = (deleted / scanned * 100.0) if scanned else 0.0
        return {
            "deals_scanned": scanned,
            "notes_deleted": deleted,
            "errors": errors,
            "runs": runs,
            "duplicate_rate": round(rate, 2),
            "days": days,
        }
    except Exception:
        return {"deals_scanned": 0, "notes_deleted": 0, "errors": 0,
                "runs": 0, "duplicate_rate": 0.0, "days": days}


def state_set(key: str, value: Any) -> bool:
    if not is_enabled():
        return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute("""
                INSERT INTO singleton_state (key, value, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=NOW()
            """, (key, json.dumps(value)))
            cn.commit()
        return True
    except Exception:
        return False
