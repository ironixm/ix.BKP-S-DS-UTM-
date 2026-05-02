"""Storage SQLite para dedup de leads de formulários (Meta + GAds).

Tabela leadform_ingested (provider, lead_id) único.
"""
from __future__ import annotations
import os
import sqlite3
import time
import json as _json
from typing import Optional

_DB_PATH = os.environ.get("LEADFORMS_DB", "/data/leadforms.sqlite")


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(_DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("""
        CREATE TABLE IF NOT EXISTS leadform_ingested (
            provider TEXT NOT NULL,
            lead_id  TEXT NOT NULL,
            form_id  TEXT,
            agendor_person_id INTEGER,
            agendor_deal_id   INTEGER,
            status   TEXT NOT NULL,           -- ok | error | duplicate | no_data
            error    TEXT,
            payload  TEXT,                    -- json original
            received_at INTEGER NOT NULL,
            processed_at INTEGER,
            PRIMARY KEY (provider, lead_id)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_lf_status ON leadform_ingested(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_lf_received ON leadform_ingested(received_at)")
    return c


def already_ingested(provider: str, lead_id: str) -> Optional[dict]:
    with _conn() as c:
        r = c.execute(
            "SELECT * FROM leadform_ingested WHERE provider=? AND lead_id=?",
            (provider, str(lead_id)),
        ).fetchone()
        return dict(r) if r else None


def record(provider: str, lead_id: str, *, form_id: str | None = None,
           agendor_person_id: int | None = None, agendor_deal_id: int | None = None,
           status: str = "ok", error: str | None = None,
           payload: dict | None = None) -> None:
    now = int(time.time())
    with _conn() as c:
        c.execute("""
            INSERT INTO leadform_ingested
                (provider, lead_id, form_id, agendor_person_id, agendor_deal_id,
                 status, error, payload, received_at, processed_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(provider, lead_id) DO UPDATE SET
                status=excluded.status,
                error=excluded.error,
                agendor_person_id=COALESCE(excluded.agendor_person_id, leadform_ingested.agendor_person_id),
                agendor_deal_id=COALESCE(excluded.agendor_deal_id, leadform_ingested.agendor_deal_id),
                processed_at=excluded.processed_at
        """, (provider, str(lead_id), form_id, agendor_person_id, agendor_deal_id,
              status, error, _json.dumps(payload, ensure_ascii=False) if payload else None,
              now, now))


def list_recent(limit: int = 50, provider: str | None = None) -> list:
    q = "SELECT * FROM leadform_ingested"
    args: tuple = ()
    if provider:
        q += " WHERE provider=?"
        args = (provider,)
    q += " ORDER BY received_at DESC LIMIT ?"
    with _conn() as c:
        return [dict(r) for r in c.execute(q, args + (limit,))]


def stats() -> dict:
    with _conn() as c:
        out = {"total": 0, "by_provider": {}, "by_status": {}}
        for r in c.execute("SELECT provider, status, COUNT(*) n FROM leadform_ingested GROUP BY provider, status"):
            out["total"] += r["n"]
            out["by_provider"].setdefault(r["provider"], 0)
            out["by_provider"][r["provider"]] += r["n"]
            out["by_status"].setdefault(r["status"], 0)
            out["by_status"][r["status"]] += r["n"]
        return out
