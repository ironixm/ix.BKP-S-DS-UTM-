"""Scheduler ad_ops: thread daemon que executa ops devidas + verifica resultados."""
from __future__ import annotations
import threading, time, traceback
from datetime import datetime, timedelta, timezone

from . import store
from . import gads_executor, meta_executor

_thread: threading.Thread | None = None
_stop = threading.Event()
LOOP_SECONDS = 60


def _exec_one(op: dict) -> None:
    oid = op["id"]
    store.update_op(oid, status=store.OP_STATUS_RUNNING)
    try:
        ex = gads_executor if op["channel"] == "gads" else meta_executor
        result = ex.execute(op["action"], op["target_type"],
                            op.get("target_id") or "", op.get("params") or {})
        ok = bool(result.get("ok"))
        executed = datetime.now(timezone.utc)
        if ok and op.get("verify_after_min") and op.get("verify_metric"):
            store.update_op(oid, status=store.OP_STATUS_VERIFYING,
                            executed_at=executed, result=result)
        else:
            store.update_op(oid, status=(store.OP_STATUS_DONE if ok else store.OP_STATUS_FAILED),
                            executed_at=executed, result=result)
            if ok and op.get("on_success"):
                _activate_next(op["on_success"])
            elif not ok and op.get("on_failure"):
                _activate_next(op["on_failure"])
    except Exception as e:
        store.update_op(oid, status=store.OP_STATUS_FAILED,
                        result={"ok": False, "error": str(e), "trace": traceback.format_exc()[-500:]})


def _verify_one(op: dict) -> None:
    oid = op["id"]
    try:
        ex = gads_executor if op["channel"] == "gads" else meta_executor
        v = ex.verify(op["verify_metric"], float(op["verify_threshold"] or 0),
                      op.get("target_id") or "")
        merged = {"exec": op.get("result"), "verify": v}
        store.update_op(oid, status=store.OP_STATUS_DONE, result=merged)
        nxt = op.get("on_success") if v.get("ok") else op.get("on_failure")
        if nxt:
            _activate_next(nxt)
    except Exception as e:
        store.update_op(oid, status=store.OP_STATUS_FAILED,
                        result={"ok": False, "error": f"verify falhou: {e}"})


def _activate_next(next_id: str) -> None:
    """Adianta a próxima op para 'agora' se ainda estiver pending."""
    op = store.get_op(next_id)
    if op and op["status"] == store.OP_STATUS_PENDING:
        store.update_op(next_id, scheduled_for=datetime.now(timezone.utc))


def _loop():
    while not _stop.is_set():
        try:
            for op in store.due_ops():
                _exec_one(op)
            for op in store.verifying_ops_due():
                _verify_one(op)
        except Exception as e:
            print(f"[ad_ops scheduler] loop err: {e}", flush=True)
        _stop.wait(LOOP_SECONDS)


def start_scheduler() -> bool:
    global _thread
    if _thread and _thread.is_alive():
        return False
    store.init_db()
    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True, name="ad_ops-scheduler")
    _thread.start()
    print("[ad_ops] scheduler started", flush=True)
    return True


def stop_scheduler():
    _stop.set()


def run_now(op_id: str) -> dict:
    """Executa imediatamente (independente do scheduled_for)."""
    op = store.get_op(op_id)
    if not op:
        return {"ok": False, "error": "op não encontrada"}
    if op["status"] != store.OP_STATUS_PENDING:
        return {"ok": False, "error": f"status atual: {op['status']}"}
    _exec_one(op)
    return {"ok": True, "op": store.get_op(op_id)}
