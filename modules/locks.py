"""File-based locks por entidade (deal, person, etc).

Uso:
    with deal_lock(deal_id):
        ... critical section (e.g. note read/write/dedup) ...

Funciona entre múltiplos workers gunicorn no mesmo container porque usa
fcntl.flock() em arquivos de /tmp/ix_locks/. NÃO funciona entre containers
distribuídos — para isso seria preciso Redis. No nosso deploy é um único
serviço com 2 workers, então fcntl é suficiente.
"""
from __future__ import annotations

import contextlib
import errno
import fcntl
import os
import time

LOCK_DIR = os.environ.get("IX_LOCK_DIR", "/tmp/ix_locks")
os.makedirs(LOCK_DIR, exist_ok=True)


@contextlib.contextmanager
def file_lock(name: str, timeout: float = 15.0, poll: float = 0.1):
    """Lock exclusivo via fcntl. Bloqueia até 'timeout' segundos."""
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))
    path = os.path.join(LOCK_DIR, f"{safe}.lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as e:
                if e.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                if time.monotonic() >= deadline:
                    # Não conseguiu — segue sem lock (best-effort) para não derrubar webhook
                    break
                time.sleep(poll)
        yield acquired
    finally:
        try:
            if acquired:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def deal_lock(deal_id, timeout: float = 15.0):
    return file_lock(f"deal_{deal_id}", timeout=timeout)
