#!/usr/bin/env python3
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Instalar – V1.0.0                              │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ modulos/mopgled/instalar.py                    │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Instalador MopGled – APP ix.BZP-DealScore-UTM-Sync
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
ASSETS_DIR = HERE / "assets"
MANIFEST_PATH = HERE / "manifests" / "mopgled.json"
LOGS_DIR = HERE / "logs"
BACKUP_DIR = HERE / "backups"
BACKUP_TTL_HOURS = 24
HEAD_SNIPPET = "{% include 'mopgled/head_include.html' %}"
SCRIPTS_SNIPPET = "{% include 'mopgled/scripts_include.html' %}"
CANDIDATE_PATTERNS = [
    "base.html",
    "base.htm",
    "base-modelo.html",
    "base-modelo.txt",
    "modelo.html",
    "modelo.txt",
    "layout.html",
]
SYNC_TOKEN = os.getenv("MOPGLED_SYNC_TOKEN") or os.getenv("ALIXIA_SYNC_TOKEN")


def colorize(message: str, code: str) -> str:
    if not sys.stdout.isatty():
        return message
    return f"\033[{code}m{message}\033[0m"


def log(msg: str, level: str = "info") -> None:
    palette = {"info": "36", "success": "32", "warn": "33", "error": "31"}
    code = palette.get(level, "36")
    print(colorize(f"[{level.upper()}] {msg}", code))


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text("utf-8"))


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def prune_old_backups() -> None:
    if not BACKUP_DIR.exists():
        return
    now = datetime.utcnow()
    for child in BACKUP_DIR.iterdir():
        if not child.is_dir():
            continue
        try:
            ts = datetime.strptime(child.name, "%Y%m%d_%H%M%S")
        except ValueError:
            continue
        if now - ts > timedelta(hours=BACKUP_TTL_HOURS):
            shutil.rmtree(child, ignore_errors=True)


def ensure_latest_package(manifest: dict) -> dict:
    module_url = manifest.get("cdn", {}).get("module_url")
    current_ts = parse_ts(manifest.get("generated_at"))
    if not module_url:
        return manifest

    try:
        headers = {"User-Agent": "MopGledInstaller/1.0"}
        if SYNC_TOKEN:
            headers["Authorization"] = f"Bearer {SYNC_TOKEN}"
        req = Request(module_url, headers=headers)
        with urlopen(req, timeout=10) as resp:  # nosec - endpoint controlado
            data = resp.read()
    except HTTPError as exc:
        if exc.code == 401:
            log("Atualização do MopGled bloqueada (401). Defina MOPGLED_SYNC_TOKEN ou ALIXIA_SYNC_TOKEN antes de rodar.", "warn")
        else:
            log(f"Não foi possível verificar atualizações do módulo ({exc}).", "warn")
        return manifest
    except URLError as exc:
        log(f"Não foi possível verificar atualizações do módulo ({exc}).", "warn")
        return manifest

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive = Path(tmp_dir) / "module.zip"
        archive.write_bytes(data)
        with zipfile.ZipFile(archive) as zf:
            manifest_member = next(
                (name for name in zf.namelist() if name.endswith("modulos/mopgled/manifests/mopgled.json")), None
            )
            if not manifest_member:
                log("Pacote remoto sem manifest, ignorando atualização.", "warn")
                return manifest
            remote_manifest = json.loads(zf.read(manifest_member).decode("utf-8"))
            remote_ts = parse_ts(remote_manifest.get("generated_at"))
            if current_ts and remote_ts and remote_ts <= current_ts:
                return manifest
            zf.extractall(Path(tmp_dir) / "pkg")
            extracted_root = next(Path(tmp_dir, "pkg").glob("*/modulos/mopgled"), None)
            if not extracted_root:
                log("Pacote remoto não contém modulos/mopgled, ignorando.", "warn")
                return manifest
            log("Atualização do MopGled encontrada. Aplicando novo pacote...", "info")
            for item in extracted_root.rglob("*"):
                rel = item.relative_to(extracted_root)
                dest = HERE / rel
                if item.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
            log("Pacote atualizado. Prosseguindo com a instalação...", "success")
            return load_manifest()


def create_backup_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def backup_file(path: Path, backup_root: Path, tracked: set[Path]) -> None:
    if path in tracked or not path.exists():
        return
    rel = path.relative_to(PROJECT_ROOT)
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    tracked.add(path)


def restore_backup(timestamp: str) -> None:
    backup_path = BACKUP_DIR / timestamp
    if not backup_path.exists():
        log(f"Backup {timestamp} não encontrado.", "error")
        sys.exit(1)
    for item in backup_path.rglob("*"):
        if item.is_dir():
            continue
        target = PROJECT_ROOT / item.relative_to(backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
    log(f"Backup {timestamp} restaurado com sucesso.", "success")


def copy_asset(asset_name: str, target: Path, touched: list[str], backup_root: Path, backed_up: set[Path]) -> None:
    source = ASSETS_DIR / asset_name
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_file(target, backup_root, backed_up)
    shutil.copy2(source, target)
    touched.append(str(target.relative_to(PROJECT_ROOT)))
    log(f"✔ Copiado {asset_name} -> {target}", "success")


def insert_snippet(content: str, snippet: str, closing_tag: str) -> tuple[str, bool]:
    if snippet in content:
        return content, False
    lower = content.lower()
    idx = lower.rfind(closing_tag)
    if idx == -1:
        return content, False
    return content[:idx] + snippet + "\n" + content[idx:], True


def patch_template(file_path: Path, backup_root: Path, backed_up: set[Path], touched: list[str]) -> None:
    if not file_path.exists():
        return
    original = file_path.read_text("utf-8")
    updated = original
    updated, head_changed = insert_snippet(updated, f"{HEAD_SNIPPET}\n", "</head>")
    updated, body_changed = insert_snippet(updated, f"{SCRIPTS_SNIPPET}\n", "</body>")
    if head_changed or body_changed:
        backup_file(file_path, backup_root, backed_up)
        file_path.write_text(updated, "utf-8")
        touched.append(str(file_path.relative_to(PROJECT_ROOT)))
        log(f"✔ Atualizado template {file_path}", "success")
    else:
        log(f"Nada para ajustar em {file_path} (snippets já presentes ou sem <head>/<body>.", "info")


def find_candidate_templates(templates_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in CANDIDATE_PATTERNS:
        path = templates_dir / pattern
        if path.exists():
            candidates.append(path)
    if candidates:
        return candidates
    fallback = list(templates_dir.glob("**/*.html"))
    return fallback[:1]


def dump_report(touched, templates_dir: Path) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "templates_dir": str(templates_dir),
        "files": touched,
    }
    (LOGS_DIR / "last-run.log").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    log(f"Relatório salvo em {LOGS_DIR / 'last-run.log'}", "success")


def apply_installation(manifest: dict) -> None:
    defaults = manifest.get("defaults", {})
    templates_dir = PROJECT_ROOT / defaults.get("templates_dir", "templates")
    app_meta = manifest.get("app", {})
    cdn_meta = manifest.get("cdn", {})

    log(f"Projeto: {PROJECT_ROOT}", "info")
    log(f"Templates alvo: {templates_dir}", "info")
    log(
        f"APP: {app_meta.get('name')} (ID {app_meta.get('id')}) – Tema {app_meta.get('theme_id')} [{app_meta.get('mode')}]",
        "info",
    )
    log(f"CSS: {cdn_meta.get('css_url')}", "info")
    log(f"JS : {cdn_meta.get('js_url')}", "info")

    touched: list[str] = []
    backup_root = create_backup_dir()
    backed_up: set[Path] = set()

    targets = [
        ("mopgled_head.html", templates_dir / "mopgled" / "head_include.html"),
        ("mopgled_scripts.html", templates_dir / "mopgled" / "scripts_include.html"),
    ]
    for asset_name, dest in targets:
        copy_asset(asset_name, dest, touched, backup_root, backed_up)

    for template_file in find_candidate_templates(templates_dir):
        patch_template(template_file, backup_root, backed_up, touched)

    dump_report(touched, templates_dir)
    log("Instalação do MopGled concluída. Abra o app e valide o layout.", "success")
    log(f"Se precisar restaurar, rode: python3 modulos/mopgled/instalar.py --restore {backup_root.name}", "info")


def main() -> None:
    parser = argparse.ArgumentParser(description="Instalador automático do MopGled.")
    parser.add_argument(
        "--restore",
        metavar="YYYYMMDD_HHMMSS",
        help="Restaura um backup gerado previamente (válido por 24h).",
    )
    args = parser.parse_args()

    prune_old_backups()
    manifest = load_manifest()
    manifest = ensure_latest_package(manifest)

    if args.restore:
        restore_backup(args.restore)
        return

    apply_installation(manifest)


if __name__ == "__main__":
    main()

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
