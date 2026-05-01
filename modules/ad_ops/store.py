"""Store de ad_ops em Postgres (reusa modules/db.py)."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from typing import Any, Optional

from modules.db import conn_ctx, is_enabled

OP_STATUS_PENDING   = "pending"
OP_STATUS_RUNNING   = "running"
OP_STATUS_DONE      = "done"
OP_STATUS_FAILED    = "failed"
OP_STATUS_CANCELLED = "cancelled"
OP_STATUS_VERIFYING = "verifying"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ad_ops (
    id                TEXT PRIMARY KEY,
    channel           TEXT NOT NULL,
    action            TEXT NOT NULL,
    target_type       TEXT NOT NULL,
    target_id         TEXT,
    target_name       TEXT NOT NULL,
    params            JSONB NOT NULL DEFAULT '{}'::jsonb,
    scheduled_for     TIMESTAMPTZ NOT NULL,
    executed_at       TIMESTAMPTZ,
    status            TEXT NOT NULL DEFAULT 'pending',
    result            JSONB,
    depends_on        TEXT,
    verify_after_min  INTEGER,
    verify_metric     TEXT,
    verify_threshold  REAL,
    on_success        TEXT,
    on_failure        TEXT,
    note              TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ad_ops_status_sched ON ad_ops (status, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_ad_ops_channel ON ad_ops (channel);
"""

_schema_ready = False


def init_db() -> bool:
    global _schema_ready
    if _schema_ready: return True
    if not is_enabled(): return False
    try:
        with conn_ctx() as cn, cn.cursor() as cur:
            cur.execute(_SCHEMA); cn.commit()
        _schema_ready = True
        return True
    except Exception as e:
        print(f"[ad_ops] init_db FAIL: {e}", flush=True)
        return False


def _row(cur, r) -> dict:
    cols = [c.name for c in cur.description]
    d = dict(zip(cols, r))
    for k in ("scheduled_for", "executed_at", "created_at", "updated_at"):
        if d.get(k):
            d[k] = d[k].astimezone(timezone.utc).isoformat() if isinstance(d[k], datetime) else str(d[k])
    return d


def enqueue(*, channel: str, action: str, target_type: str, target_name: str,
            target_id: Optional[str] = None, params: Optional[dict] = None,
            scheduled_for: Optional[datetime] = None, depends_on: Optional[str] = None,
            verify_after_min: Optional[int] = None, verify_metric: Optional[str] = None,
            verify_threshold: Optional[float] = None,
            on_success: Optional[str] = None, on_failure: Optional[str] = None,
            note: Optional[str] = None, op_id: Optional[str] = None) -> str:
    init_db()
    oid = op_id or uuid.uuid4().hex[:12]
    sched = scheduled_for or datetime.now(timezone.utc)
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute("""
        INSERT INTO ad_ops (id, channel, action, target_type, target_id, target_name,
            params, scheduled_for, status, depends_on, verify_after_min,
            verify_metric, verify_threshold, on_success, on_failure, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, 'pending', %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """, (oid, channel, action, target_type, target_id, target_name,
              json.dumps(params or {}), sched, depends_on, verify_after_min,
              verify_metric, verify_threshold, on_success, on_failure, note))
        cn.commit()
    return oid


def list_ops(status: Optional[str] = None, channel: Optional[str] = None,
             limit: int = 200) -> list[dict]:
    init_db()
    sql = "SELECT * FROM ad_ops"
    where, args = [], []
    if status:  where.append("status = %s");  args.append(status)
    if channel: where.append("channel = %s"); args.append(channel)
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY scheduled_for ASC, created_at ASC LIMIT %s"
    args.append(limit)
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute(sql, args)
        return [_row(cur, r) for r in cur.fetchall()]


def get_op(op_id: str) -> Optional[dict]:
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute("SELECT * FROM ad_ops WHERE id = %s", (op_id,))
        r = cur.fetchone()
        return _row(cur, r) if r else None


def update_op(op_id: str, **fields) -> None:
    if not fields: return
    sets, args = [], []
    for k, v in fields.items():
        if k == "result" and v is not None:
            sets.append(f"{k} = %s::jsonb"); args.append(json.dumps(v))
        else:
            sets.append(f"{k} = %s"); args.append(v)
    sets.append("updated_at = NOW()")
    args.append(op_id)
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute(f"UPDATE ad_ops SET {', '.join(sets)} WHERE id = %s", args)
        cn.commit()


def cancel_op(op_id: str) -> bool:
    op = get_op(op_id)
    if not op or op["status"] not in (OP_STATUS_PENDING, OP_STATUS_VERIFYING):
        return False
    update_op(op_id, status=OP_STATUS_CANCELLED)
    return True


def due_ops() -> list[dict]:
    """Pending com scheduled_for <= now, sem dep pendente."""
    init_db()
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute("""
        SELECT * FROM ad_ops
        WHERE status = 'pending' AND scheduled_for <= NOW()
        ORDER BY scheduled_for ASC LIMIT 50
        """)
        rows = [_row(cur, r) for r in cur.fetchall()]
    out = []
    for r in rows:
        if r.get("depends_on"):
            dep = get_op(r["depends_on"])
            if not dep or dep["status"] != OP_STATUS_DONE:
                continue
        out.append(r)
    return out


def verifying_ops_due() -> list[dict]:
    init_db()
    with conn_ctx() as cn, cn.cursor() as cur:
        cur.execute("""
        SELECT * FROM ad_ops
        WHERE status = 'verifying'
          AND verify_after_min IS NOT NULL
          AND executed_at IS NOT NULL
          AND executed_at + (verify_after_min || ' minutes')::interval <= NOW()
        """)
        return [_row(cur, r) for r in cur.fetchall()]
