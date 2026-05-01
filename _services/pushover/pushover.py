#!/usr/bin/env python3
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Pushover – V1.0.1                              │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-12 - 07:53         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _services/pushover/pushover.py                 │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.1 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝


from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE_PATH = HERE / "state.json"
PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json"
ENV_FILES = [
    ROOT / "/_services/pushover/.env.pushover",
    ROOT / ".env",
    ROOT / ".env.local",
    ROOT / ".env.dev",
    ROOT / ".env.prod",
]


def _load_env_files() -> None:
    for path in ENV_FILES:
        if not path.exists():
            continue
        for raw in path.read_text("utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _state_from_file() -> dict:
    if not STATE_PATH.exists():
        return {"enabled": True}
    try:
        data = json.loads(STATE_PATH.read_text("utf-8"))
    except Exception:
        return {"enabled": True}
    if not isinstance(data, dict):
        return {"enabled": True}
    return {"enabled": bool(data.get("enabled", True))}


def _write_state(enabled: bool) -> None:
    STATE_PATH.write_text(json.dumps({"enabled": enabled}, indent=2), "utf-8")


def _env_flag_enabled() -> bool | None:
    raw = os.getenv("PUSHOVER_ENABLED")
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return None


def is_enabled() -> bool:
    env_flag = _env_flag_enabled()
    if env_flag is not None:
        return env_flag
    return _state_from_file().get("enabled", True)


def resolve_keys() -> tuple[str | None, str | None]:
    user_key = os.getenv("PUSHOVER_USER_KEY")
    api_token = os.getenv("PUSHOVER_API_TOKEN") or os.getenv("PUSHOVER_API_KEY")
    return user_key, api_token


def send_notification(
    title: str,
    message: str,
    priority: int = 0,
    sound: str | None = None,
    url: str | None = None,
    url_title: str | None = None,
) -> int:
    if not is_enabled():
        print("[pushover] notificacoes pausadas")
        return 0

    user_key, api_token = resolve_keys()
    if not user_key or not api_token:
        print("[pushover] chaves ausentes (PUSHOVER_USER_KEY / PUSHOVER_API_TOKEN)")
        return 1

    payload = {
        "token": api_token,
        "user": user_key,
        "title": title,
        "message": message,
        "priority": str(priority),
    }
    if sound:
        payload["sound"] = sound
    if url:
        payload["url"] = url
    if url_title:
        payload["url_title"] = url_title

    data = urlencode(payload).encode("utf-8")
    req = Request(PUSHOVER_ENDPOINT, data=data)

    try:
        with urlopen(req, timeout=10) as resp:  # nosec - endpoint conhecido
            if resp.status >= 200 and resp.status < 300:
                print("[pushover] enviado")
                return 0
            print(f"[pushover] falha status={resp.status}")
            return 1
    except Exception as exc:
        print(f"[pushover] erro: {exc}")
        return 1


def main() -> int:
    _load_env_files()

    parser = argparse.ArgumentParser(description="Micro-servico Pushover")
    sub = parser.add_subparsers(dest="command", required=True)

    send_cmd = sub.add_parser("send", help="Enviar notificacao")
    send_cmd.add_argument("--title", required=True, help="Titulo")
    send_cmd.add_argument("--message", required=True, help="Mensagem")
    send_cmd.add_argument("--priority", type=int, default=0, help="Prioridade (-2 a 2)")
    send_cmd.add_argument("--sound", help="Som do Pushover")
    send_cmd.add_argument("--url", help="URL opcional")
    send_cmd.add_argument("--url-title", help="Titulo da URL")

    sub.add_parser("enable", help="Ativar notificacoes")
    sub.add_parser("disable", help="Pausar notificacoes")
    sub.add_parser("status", help="Status atual")

    args = parser.parse_args()

    if args.command == "enable":
        _write_state(True)
        print("[pushover] ativado")
        return 0
    if args.command == "disable":
        _write_state(False)
        print("[pushover] pausado")
        return 0
    if args.command == "status":
        print("[pushover] ativo" if is_enabled() else "[pushover] pausado")
        return 0
    if args.command == "send":
        return send_notification(
            title=args.title,
            message=args.message,
            priority=args.priority,
            sound=args.sound,
            url=args.url,
            url_title=args.url_title,
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())

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
