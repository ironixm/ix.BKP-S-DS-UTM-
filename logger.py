# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Logger – V1.0.0                                │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ logger.py                                      │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

# logger.py
import json
import os
from datetime import datetime, timezone
from typing import Any

# Pode ser sobrescrito por env IX_DATA_DIR (volume persistente do Coolify).
_DATA_DIR = os.environ.get("IX_DATA_DIR", "").strip()
if _DATA_DIR:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        LOG_FILE = os.path.join(_DATA_DIR, "events.log")
    except Exception:
        LOG_FILE = "events.log"
else:
    LOG_FILE = "events.log"


def log_event(event_type: str, payload: dict[str, Any]) -> None:
    record = {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    line = json.dumps(record, ensure_ascii=False)

    # stdout (continua aparecendo no log do container)
    print(line)

    # 1) Postgres (fonte de verdade) -- best-effort
    try:
        from modules import db as _db
        if _db.is_enabled():
            _db.insert_event(
                type=event_type,
                deal_id=payload.get("deal_id"),
                person_id=payload.get("person_id"),
                org_id=payload.get("org_id"),
                stage_id=payload.get("stage_id"),
                score=payload.get("score"),
                parts=payload.get("parts"),
                source=payload.get("source"),
                payload={k: v for k, v in payload.items()
                         if k not in {"deal_id", "person_id", "org_id", "stage_id", "score", "parts", "source"}},
            )
    except Exception as e:  # noqa: BLE001
        print(f"[logger] db insert FAIL: {e}", flush=True)

    # 2) arquivo (fallback / debug local)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

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
