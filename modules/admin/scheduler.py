"""Scheduler de rotinas batch — gerencia agendamentos persistidos em JSON.

Sem dependências externas (sem APScheduler) — rodamos em background thread.
Persistência: tmp/scheduler_jobs.json
Cada job: id, batch_size, freq_minutes, date_from, date_to, date_field,
status, created_at, last_run_at, next_run_at, processed, total_estimated.

Limites Pipedrive:
- 100 req / 10s por usuário (≈10 req/s)
- 30k req/dia (planos Advanced+) — usar `_request` que já tem rate limit
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = os.environ.get("IX_DATA_DIR", "").strip()
if _DATA_DIR:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        JOBS_FILE = Path(_DATA_DIR) / "scheduler_jobs.json"
    except Exception:
        JOBS_FILE = ROOT / "tmp" / "scheduler_jobs.json"
else:
    JOBS_FILE = ROOT / "tmp" / "scheduler_jobs.json"
JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Limites
PIPEDRIVE_DAILY_TOKEN_LIMIT = int(os.environ.get("PD_DAILY_LIMIT", "30000"))
# Por deal processado consumimos ~10 chamadas (read deal + person + notes + flow + update + add/upd note + dedup + prefill)
TOKENS_PER_DEAL = int(os.environ.get("TOKENS_PER_DEAL", "10"))
# Preset ideal: 80 deals a cada 10min → 80*4=320 req/10min → 46k/dia (acima!) → 60 deals
PRESET_BATCH_SIZE = int(os.environ.get("BATCH_PRESET_SIZE", "60"))
PRESET_FREQ_MIN = int(os.environ.get("BATCH_PRESET_FREQ_MIN", "10"))
MAX_DAILY_TOKENS_RECOMMENDED = int(PIPEDRIVE_DAILY_TOKEN_LIMIT * 0.7)  # margem 30%

_lock = threading.Lock()
_thread_started = False


# -------- persistence --------

# -------- persistence --------

def _load() -> list[dict]:
    # Tenta DB primeiro
    try:
        from modules import db as _db
        if _db.is_enabled():
            jobs = _db.jobs_load_all()
            if jobs is not None:
                return jobs
    except Exception as e:  # noqa: BLE001
        print(f"[scheduler] db load FAIL, fallback JSON: {e}", flush=True)
    # Fallback arquivo
    if not JOBS_FILE.exists():
        return []
    try:
        return json.loads(JOBS_FILE.read_text())
    except Exception:
        return []


def _save(jobs: list[dict]) -> None:
    # DB sync
    try:
        from modules import db as _db
        if _db.is_enabled():
            _db.jobs_save_all(jobs)
    except Exception as e:  # noqa: BLE001
        print(f"[scheduler] db save FAIL: {e}", flush=True)
    # Arquivo (backup)
    try:
        JOBS_FILE.write_text(json.dumps(jobs, indent=2, default=str))
    except Exception:
        pass


def list_jobs() -> list[dict]:
    return _load()


# -------- validation --------

def estimate_daily_tokens(batch_size: int, freq_minutes: int) -> int:
    runs_per_day = (24 * 60) // max(1, freq_minutes)
    return runs_per_day * batch_size * TOKENS_PER_DEAL


def validate_config(batch_size: int, freq_minutes: int) -> dict:
    daily = estimate_daily_tokens(batch_size, freq_minutes)
    return {
        "estimated_daily_tokens": daily,
        "limit": PIPEDRIVE_DAILY_TOKEN_LIMIT,
        "recommended_max": MAX_DAILY_TOKENS_RECOMMENDED,
        "ok": daily <= MAX_DAILY_TOKENS_RECOMMENDED,
        "warning": (
            None if daily <= MAX_DAILY_TOKENS_RECOMMENDED
            else f"⚠️  Estimativa {daily:,} req/dia ultrapassa recomendado {MAX_DAILY_TOKENS_RECOMMENDED:,} (70% do limite {PIPEDRIVE_DAILY_TOKEN_LIMIT:,})."
        ),
        "blocked": daily > PIPEDRIVE_DAILY_TOKEN_LIMIT,
    }


# -------- create / cancel --------

def create_job(*, batch_size: int, freq_minutes: int, date_from: str, date_to: str,
               date_field: str = "update_time",
               with_notes: bool = True, with_prefill: bool = False,
               with_dedup: bool = False, status_filter: str = "all_not_deleted",
               sort_dir: str = "DESC", cursor_start: int = 0) -> dict:
    val = validate_config(batch_size, freq_minutes)
    if val["blocked"]:
        raise ValueError(f"Configuração bloqueada: {val['estimated_daily_tokens']:,} req/dia > limite {PIPEDRIVE_DAILY_TOKEN_LIMIT:,}")

    sort_dir = (sort_dir or "DESC").upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"

    job = {
        "id": uuid.uuid4().hex[:8],
        "batch_size": batch_size,
        "freq_minutes": freq_minutes,
        "date_from": date_from,
        "date_to": date_to,
        "date_field": date_field,
        "status_filter": status_filter,
        "with_notes": with_notes,
        "with_prefill": with_prefill,
        "with_dedup": with_dedup,
        "sort_dir": sort_dir,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run_at": None,
        "next_run_at": datetime.now(timezone.utc).isoformat(),
        "processed": 0,
        "errors": 0,
        "cursor_start": int(cursor_start or 0),
        "estimated_daily_tokens": val["estimated_daily_tokens"],
    }
    with _lock:
        jobs = _load()
        jobs.append(job)
        _save(jobs)
    return job


def resume_job(job_id: str, *, reset_cursor: bool = False) -> bool:
    """Reabre um job completed/cancelled como pending, opcionalmente zerando o cursor."""
    with _lock:
        jobs = _load()
        for j in jobs:
            if j["id"] == job_id and j["status"] in ("completed", "cancelled"):
                j["status"] = "pending"
                if reset_cursor:
                    j["cursor_start"] = 0
                j["next_run_at"] = (datetime.now(timezone.utc) + timedelta(minutes=int(j.get("freq_minutes", 1)))).isoformat()
                _save(jobs)
                return True
    return False


def cancel_job(job_id: str) -> bool:
    with _lock:
        jobs = _load()
        for j in jobs:
            if j["id"] == job_id and j["status"] in ("pending", "running"):
                j["status"] = "cancelled"
                _save(jobs)
                return True
    return False


def delete_job(job_id: str) -> bool:
    with _lock:
        jobs = _load()
        new = [j for j in jobs if j["id"] != job_id]
        if len(new) != len(jobs):
            _save(new)
            return True
    return False


# -------- runner --------

_QUOTA_RE = re.compile(r"bloqueado por (\d+)s|Retry-After[^0-9]+(\d+)|429.*?(\d{2,})")


def _quota_retry_after(err: Exception) -> int | None:
    """Se a exceção for um 429 com Retry-After, retorna segundos para pausar."""
    msg = str(err) or ""
    if "429" not in msg and "rate limit" not in msg.lower() and "quota" not in msg.lower():
        return None
    m = _QUOTA_RE.search(msg)
    if not m:
        return 600  # fallback: pausa 10min
    for g in m.groups():
        if g and g.isdigit():
            return int(g)
    return 600


def _pause_job_for_quota(job: dict, retry_after_s: int) -> None:
    """Pausa job: ajusta next_run_at para now + retry_after + 30s safety."""
    from logger import log_event
    pause = max(60, int(retry_after_s)) + 30
    until = datetime.now(timezone.utc) + timedelta(seconds=pause)
    job["next_run_at"] = until.isoformat()
    job["quota_pause_until"] = until.isoformat()
    log_event("scheduler_quota_pause", {
        "job_id": job["id"],
        "retry_after_s": retry_after_s,
        "pause_s": pause,
        "until": until.isoformat(),
    })


def _run_one_batch(job: dict) -> tuple[int, int]:
    """Processa um batch. Retorna (processed, errors)."""
    from pd_api import _request, get_deal, dedup_auto_notes_for_deal
    from logger import log_event

    processed = 0
    errors = 0
    field = job.get("date_field") or "update_time"
    status_filter = job.get("status_filter") or "all_not_deleted"
    with_notes = bool(job.get("with_notes", True))
    with_prefill = bool(job.get("with_prefill", False))
    with_dedup = bool(job.get("with_dedup", False))

    # Imports dependentes do modo
    if with_notes:
        # process_deal faz score+title+notes+lock+dedup pré/pós
        from main import process_deal
    else:
        from dealscore.deal_score import FIELD_IDS, build_dealscore_payload, compute_deal_score
        from dealscore.deal_score_rules import apply_emoji_prefix
        from pd_api import get_person, update_deal

    if with_prefill:
        from scripts.prefill_dealscore_fields import process_one as prefill_one  # type: ignore

    sort_dir = (job.get("sort_dir") or "DESC").upper()
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "DESC"
    try:
        resp = _request("/deals", params={
            "start": job.get("cursor_start", 0),
            "limit": job["batch_size"],
            "status": status_filter,
            "sort": f"{field} {sort_dir}",
        })
        deals = resp.get("data") or []
        more_items = bool(((resp.get("additional_data") or {}).get("pagination") or {}).get("more_items_in_collection"))
    except Exception as e:
        ra = _quota_retry_after(e)
        if ra is not None:
            _pause_job_for_quota(job, ra)
            log_event("scheduler_error", {"job_id": job["id"], "error": str(e)[:200], "quota_pause_s": ra})
            return 0, 0
        log_event("scheduler_error", {"job_id": job["id"], "error": str(e)[:200]})
        return 0, 1

    df = job.get("date_from")
    dt = job.get("date_to")

    for stub in deals:
        deal_id = stub.get("id")
        if not deal_id:
            continue
        ts = stub.get(field)
        if ts and df and ts[:10] < df:
            continue
        if ts and dt and ts[:10] > dt:
            continue

        try:
            if with_notes:
                # Pipeline completo: score + title + notes + dedup (com lock)
                deal_full = get_deal(deal_id) or {}
                process_deal(deal_full, mode="write")
            else:
                deal_full = get_deal(deal_id) or {}
                person = get_person(deal_full.get("person_id")) if deal_full.get("person_id") else None
                score = compute_deal_score(deal_full, person, FIELD_IDS)
                payload = build_dealscore_payload(score.total)
                title = deal_full.get("title") or ""
                new_title = apply_emoji_prefix(title, score.total)
                if new_title != title:
                    payload["title"] = new_title
                update_deal(deal_id, payload)
                log_event("deal_score", {
                    "source": "scheduler", "deal_id": deal_id,
                    "person_id": deal_full.get("person_id"),
                    "stage_id": deal_full.get("stage_id"),
                    "score": score.total, "parts": score.parts,
                    "job_id": job["id"],
                })

            if with_prefill:
                try:
                    prefill_one(deal_full, dry_run=False, with_headcount=True)
                except Exception as pe:
                    log_event("scheduler_prefill_error", {"job_id": job["id"], "deal_id": deal_id, "error": str(pe)[:200]})

            if with_dedup:
                try:
                    dedup_auto_notes_for_deal(deal_id)
                except Exception as de:
                    log_event("scheduler_dedup_error", {"job_id": job["id"], "deal_id": deal_id, "error": str(de)[:200]})

            processed += 1
        except Exception as e:
            ra = _quota_retry_after(e)
            if ra is not None:
                _pause_job_for_quota(job, ra)
                log_event("scheduler_deal_error", {"job_id": job["id"], "deal_id": deal_id, "error": str(e)[:200], "quota_pause_s": ra})
                # aborta batch — não conta como erro do deal
                job["cursor_start"] = job.get("cursor_start", 0) + processed
                return processed, errors
            errors += 1
            log_event("scheduler_deal_error", {"job_id": job["id"], "deal_id": deal_id, "error": str(e)[:200]})

    job["cursor_start"] = job.get("cursor_start", 0) + len(deals)

    # Fast-forward adaptativo: se NENHUM deal do batch caiu na janela → pula proporcional à distância
    # ASC: cursor atrás de date_from / DESC: cursor à frente de date_to
    if processed == 0 and deals:
        from datetime import datetime as _dt
        def _days_off(ts_str: str, ref: str) -> int:
            try:
                a = _dt.fromisoformat(ts_str[:10]); b = _dt.fromisoformat(ref)
                return abs((a - b).days)
            except Exception:
                return 0
        last_ts = (deals[-1].get(field) or "")[:10]
        step = 200
        if sort_dir == "ASC" and df and last_ts and last_ts < df:
            d = _days_off(last_ts, df)
            step = 2000 if d > 90 else (1000 if d > 30 else 200)
            job["cursor_start"] += step
        elif sort_dir == "DESC" and dt and last_ts and last_ts > dt:
            d = _days_off(last_ts, dt)
            step = 2000 if d > 90 else (1000 if d > 30 else 200)
            job["cursor_start"] += step

    # Early-stop: passou pra fora do range definitivamente
    if deals:
        if sort_dir == "ASC" and dt:
            first_ts = (deals[0].get(field) or "")[:10]
            if first_ts and first_ts > dt:
                job["status"] = "completed"
                return processed, errors
        elif sort_dir == "DESC" and df:
            first_ts = (deals[0].get(field) or "")[:10]
            if first_ts and first_ts < df:
                job["status"] = "completed"
                return processed, errors

    if not deals or not more_items:
        job["status"] = "completed"
    return processed, errors


def run_job_now(job_id: str, max_iters: int = 1) -> dict:
    """Força execução imediata de um job (até max_iters batches consecutivos).

    Útil para acelerar fast-forward sem esperar 10min entre batches.
    """
    out = {"job_id": job_id, "iters": 0, "processed": 0, "errors": 0, "status": None}
    with _lock:
        jobs = _load()
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return {"error": "not found", **out}
    if job["status"] not in ("pending", "running"):
        return {"error": f"status={job['status']}", **out}

    now = datetime.now(timezone.utc)
    for _ in range(max(1, min(max_iters, 50))):
        if job["status"] == "completed":
            break
        p, e = _run_one_batch(job)
        job["processed"] = job.get("processed", 0) + p
        job["errors"] = job.get("errors", 0) + e
        job["last_run_at"] = now.isoformat()
        out["iters"] += 1
        out["processed"] += p
        out["errors"] += e
        out["cursor_start"] = job.get("cursor_start", 0)
        if job["status"] == "completed":
            break

    if job["status"] != "completed":
        job["status"] = "pending"
        default_next = (now + timedelta(minutes=job["freq_minutes"])).isoformat()
        pq = job.get("quota_pause_until")
        if pq and pq > default_next:
            job["next_run_at"] = pq
        else:
            job["next_run_at"] = default_next

    with _lock:
        _save(jobs)
    out["status"] = job["status"]
    return out


def _scheduler_loop():
    while True:
        try:
            with _lock:
                jobs = _load()
            now = datetime.now(timezone.utc)
            changed = False
            for job in jobs:
                if job["status"] not in ("pending", "running"):
                    continue
                next_run = job.get("next_run_at")
                if next_run:
                    try:
                        nr = datetime.fromisoformat(next_run.replace("Z", "+00:00"))
                    except Exception:
                        nr = now
                    if nr > now:
                        continue
                # Run
                job["status"] = "running"
                with _lock:
                    _save(jobs)
                p, e = _run_one_batch(job)
                job["processed"] = job.get("processed", 0) + p
                job["errors"] = job.get("errors", 0) + e
                job["last_run_at"] = now.isoformat()
                if job["status"] != "completed":
                    job["status"] = "pending"
                    default_next = (now + timedelta(minutes=job["freq_minutes"])).isoformat()
                    # Respeita pause de quota se for mais distante
                    pq = job.get("quota_pause_until")
                    if pq and pq > default_next:
                        job["next_run_at"] = pq
                    else:
                        job["next_run_at"] = default_next
                changed = True
            if changed:
                with _lock:
                    _save(jobs)
        except Exception as e:
            try:
                from logger import log_event
                log_event("scheduler_loop_error", {"error": str(e)[:200]})
            except Exception:
                pass
        time.sleep(30)


def start_scheduler() -> None:
    global _thread_started
    if _thread_started:
        return
    _thread_started = True
    t = threading.Thread(target=_scheduler_loop, daemon=True, name="madmode-scheduler")
    t.start()


# ===========================
# Prefill DealScore fields
# ===========================

_prefill_state: dict = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "limit": 0,
    "processed": 0,
    "updated": 0,
    "skipped_manual": 0,
    "skipped_empty": 0,
    "errors": 0,
    "last_log_lines": [],
    "args": {},
    "exit_code": None,
}
_prefill_lock = threading.Lock()


def prefill_status() -> dict:
    with _prefill_lock:
        return dict(_prefill_state)


def start_prefill(limit: int = 200, dry_run: bool = False,
                  with_headcount: bool = False, status: str = "open",
                  only: str = "") -> dict:
    """Dispara o script scripts/prefill_dealscore_fields.py em subprocess."""
    from pathlib import Path
    with _prefill_lock:
        if _prefill_state["running"]:
            return {"ok": False, "error": "Prefill já está rodando", "state": dict(_prefill_state)}

    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "prefill_dealscore_fields.py"
    if not script.exists():
        return {"ok": False, "error": f"script não encontrado: {script}"}

    cmd = [sys.executable, str(script), "--limit", str(limit), "--status", status]
    if dry_run: cmd.append("--dry-run")
    if with_headcount: cmd.append("--with-headcount")
    if only: cmd += ["--only", only]

    args = {"limit": limit, "dry_run": dry_run, "with_headcount": with_headcount,
            "status": status, "only": only, "cmd": " ".join(cmd[2:])}

    def _run():
        with _prefill_lock:
            _prefill_state.update({
                "running": True, "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None, "limit": limit, "processed": 0, "updated": 0,
                "skipped_manual": 0, "skipped_empty": 0, "errors": 0,
                "last_log_lines": [], "args": args, "exit_code": None,
            })
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    cwd=str(repo_root), text=True, bufsize=1)
            tail: list[str] = []
            for line in proc.stdout:
                line = line.rstrip()
                tail.append(line)
                if len(tail) > 200: tail = tail[-200:]
                with _prefill_lock:
                    _prefill_state["last_log_lines"] = list(tail)
                    if "[OK]" in line or "[DRY]" in line:
                        _prefill_state["updated"] += 1
                    if line.startswith("[ERR]"):
                        _prefill_state["errors"] += 1
                    m = re.search(r"deals vistos:\s+(\d+)", line)
                    if m: _prefill_state["processed"] = int(m.group(1))
                    m = re.search(r"skip \(sem inferência\):\s+(\d+)", line)
                    if m: _prefill_state["skipped_empty"] = int(m.group(1))
                    m = re.search(r"skip \(editado manual\):\s+(\d+)", line)
                    if m: _prefill_state["skipped_manual"] = int(m.group(1))
            rc = proc.wait()
            with _prefill_lock:
                _prefill_state["exit_code"] = rc
        finally:
            with _prefill_lock:
                _prefill_state["running"] = False
                _prefill_state["finished_at"] = datetime.now(timezone.utc).isoformat()

    threading.Thread(target=_run, daemon=True, name="madmode-prefill").start()
    return {"ok": True, "args": args}


def prefill_status() -> dict:
    with _prefill_lock:
        return dict(_prefill_state)


# =====================================================
# Notes Dedup (limpeza de duplicatas)
# =====================================================

_dedup_lock = threading.Lock()
_dedup_state = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "deals_with_dupes": 0,
    "notes_deleted": 0,
    "errors": 0,
    "last_log_lines": [],
    "exit_code": None,
    "args": {},
    # Estimativa do último scan (para o painel)
    "last_estimate": None,  # {"sample_notes": N, "auto_notes": A, "deals_with_dupes": D, "extra_dupes": X, "ratio": pct, "ts": iso}
}


def dedup_status() -> dict:
    with _dedup_lock:
        return dict(_dedup_state)


def estimate_dedup(sample_pages: int = 1, page_size: int = 500) -> dict:
    """Lê uma amostra das notas mais recentes do Pipedrive para estimar o
    grau de duplicação automática. Bem leve: 1 página = ~1 request."""
    from collections import defaultdict
    from pd_api import _request
    from notes_builder import _is_auto_note

    by_deal = defaultdict(int)
    sample = 0
    for i in range(sample_pages):
        j = _request("/notes", params={
            "start": i * page_size, "limit": page_size, "sort": "add_time DESC",
        })
        data = j.get("data") or []
        sample += len(data)
        for n in data:
            did = n.get("deal_id")
            if did and _is_auto_note(n.get("content") or ""):
                by_deal[did] += 1
        if not (j.get("additional_data", {}).get("pagination", {}) or {}).get("more_items_in_collection"):
            break

    auto_total = sum(by_deal.values())
    deals_with_dupes = sum(1 for c in by_deal.values() if c > 1)
    extra = sum(c - 1 for c in by_deal.values() if c > 1)
    ratio = round(extra * 100.0 / auto_total, 1) if auto_total else 0.0
    out = {
        "sample_notes": sample,
        "auto_notes": auto_total,
        "deals_in_sample": len(by_deal),
        "deals_with_dupes": deals_with_dupes,
        "extra_dupes": extra,
        "ratio_pct": ratio,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with _dedup_lock:
        _dedup_state["last_estimate"] = out
    return out


def start_dedup(deal_id: str | int | None = None,
                sleep_between: float = 1.0) -> dict:
    """Dispara o script clean_duplicate_notes em background.

    Se deal_id for fornecido, limpa apenas esse deal; senão roda em modo 'all'.
    """
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "clean_duplicate_notes.py"
    if not script.exists():
        return {"ok": False, "error": f"script não encontrado: {script}"}

    with _dedup_lock:
        if _dedup_state["running"]:
            return {"ok": False, "error": "dedup já em execução"}

    target = str(deal_id) if deal_id else "all"
    cmd = [sys.executable, str(script), target]
    args = {"target": target, "sleep_between": sleep_between}

    def _run():
        with _dedup_lock:
            _dedup_state.update({
                "running": True, "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None, "deals_with_dupes": 0, "notes_deleted": 0,
                "errors": 0, "last_log_lines": [], "exit_code": None, "args": args,
            })
        try:
            env = dict(os.environ)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    cwd=str(repo_root), text=True, bufsize=1, env=env)
            tail: list[str] = []
            for line in proc.stdout:
                line = line.rstrip()
                tail.append(line)
                if len(tail) > 300: tail = tail[-300:]
                with _dedup_lock:
                    _dedup_state["last_log_lines"] = list(tail)
                    if "🗑️" in line or "deletada" in line:
                        _dedup_state["notes_deleted"] += 1
                    if "❌" in line:
                        _dedup_state["errors"] += 1
                    m = re.search(r"(\d+)\s+deals com notas autom", line)
                    if m: _dedup_state["deals_with_dupes"] = int(m.group(1))
            rc = proc.wait()
            with _dedup_lock:
                _dedup_state["exit_code"] = rc
        except Exception as e:
            with _dedup_lock:
                _dedup_state["errors"] += 1
                _dedup_state["last_log_lines"].append(f"[FATAL] {e}")
        finally:
            with _dedup_lock:
                _dedup_state["running"] = False
                _dedup_state["finished_at"] = datetime.now(timezone.utc).isoformat()

    threading.Thread(target=_run, daemon=True, name="madmode-dedup").start()
    return {"ok": True, "args": args}
