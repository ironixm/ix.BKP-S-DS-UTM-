"""ad_ops — Agendador de operações de mídia (GAds + Meta).

Pipeline:
  enqueue → scheduler tick (1min) → executor → verify (depois de N min) → next op.

Persistência: Postgres (tabela ad_ops) — usa modules/db.py.
"""
from .store import (
    init_db, enqueue, list_ops, get_op, cancel_op,
    OP_STATUS_PENDING, OP_STATUS_DONE, OP_STATUS_FAILED, OP_STATUS_CANCELLED,
)
from .scheduler import start_scheduler as start_ad_ops_scheduler
from .routes import bp as ad_ops_bp

__all__ = [
    "init_db", "enqueue", "list_ops", "get_op", "cancel_op",
    "start_ad_ops_scheduler", "ad_ops_bp",
    "OP_STATUS_PENDING", "OP_STATUS_DONE", "OP_STATUS_FAILED", "OP_STATUS_CANCELLED",
]
