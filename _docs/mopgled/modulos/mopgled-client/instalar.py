#!/usr/bin/env python3
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Instalar – V1.0.0                              │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:16         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/modulos/mopgled-client/instal... │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Instalador MopGled Client – APP ix.BZP-DealScore-UTM-Sync
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ASSETS_DIR = HERE / "assets"
MANIFEST_PATH = HERE / "manifests" / "mopgled.json"
LOGS_DIR = HERE / "logs"
BACKUP_DIR = HERE / "backups"
BACKUP_TTL_HOURS = 24
TEMPLATE_NAMESPACE = "mopgled"
HEAD_SNIPPET_INCLUDE = "{% include 'mopgled/head_include.html' %}"
SCRIPTS_SNIPPET_INCLUDE = "{% include 'mopgled/scripts_include.html' %}"
PROJECT_TEMPLATE_DIRNAME = "project_template"
CANDIDATE_PATTERNS = [
    "base.html",
    "base.htm",
    "base-modelo.html",
    "base-modelo.txt",
    "layout.html",
    "layout.htm",
    "master.html",
    "index.html",
]
COMMON_TEMPLATE_DIRS = [
    "templates",
    "template",
    "views",
    "app/templates",
    "src/templates",
    "resources/views",
]
SKIP_SCAN_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}
DOTENV_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    ".env.prod",
]


def colorize(message: str, code: str) -> str:
    if not sys.stdout.isatty():
        return message
    return f"\033[{code}m{message}\033[0m"


def log(msg: str, level: str = "info") -> None:
    palette = {"info": "36", "success": "32", "warn": "33", "error": "31"}
    code = palette.get(level, "36")
    print(colorize(f"[{level.upper()}] {msg}", code))


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        log(f"Manifest não encontrado em {MANIFEST_PATH}", "error")
        sys.exit(1)
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


def read_dotenv(path: Path) -> dict:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            data[key] = value
    return data


def write_dotenv(path: Path, key: str, value: str) -> None:
    existing = read_dotenv(path)
    existing[key] = value
    lines = []
    if path.exists():
        for raw in path.read_text("utf-8").splitlines():
            if not raw.strip() or raw.strip().startswith("#") or "=" not in raw:
                lines.append(raw)
                continue
            k, _ = raw.split("=", 1)
            if k.strip() == key:
                continue
            lines.append(raw)
    lines.append(f"{key}={value}")
    path.write_text("\n".join(lines).rstrip() + "\n", "utf-8")


def prompt_input(question: str, default: str | None = None) -> str:
    if not sys.stdin.isatty():
        return default or ""
    if default:
        prompt = f"{question} [{default}]: "
    else:
        prompt = f"{question}: "
    value = input(prompt).strip()
    return value or (default or "")


def prompt_yes_no(question: str, default: bool = False) -> bool:
    if not sys.stdin.isatty():
        return default
    suffix = "S/n" if default else "s/N"
    while True:
        value = input(f"{question} ({suffix}): ").strip().lower()
        if not value:
            return default
        if value in {"s", "sim", "y", "yes"}:
            return True
        if value in {"n", "nao", "não", "no"}:
            return False


def prompt_choice(title: str, options: list[str], default_index: int = 0) -> int:
    log(title, "info")
    for idx, opt in enumerate(options, start=1):
        print(f"  {idx}. {opt}")
    if not sys.stdin.isatty():
        return default_index
    value = input(f"Escolha [padrão {default_index + 1}]: ").strip()
    if not value:
        return default_index
    try:
        selected = int(value) - 1
    except ValueError:
        return default_index
    if 0 <= selected < len(options):
        return selected
    return default_index


def looks_like_project(path: Path) -> bool:
    markers = [
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "manage.py",
        "app.py",
        "wsgi.py",
        "templates",
        "views",
        "static",
    ]
    return any((path / marker).exists() for marker in markers)


def resolve_project_root(project_arg: str | None, interactive: bool, allow_create: bool = False) -> Path:
    if project_arg:
        path = Path(project_arg).expanduser().resolve()
        if not path.exists():
            if allow_create:
                path.mkdir(parents=True, exist_ok=True)
            else:
                log(f"Projeto não encontrado: {path}", "error")
                sys.exit(1)
        return path
    candidate = None
    if len(HERE.parents) >= 2 and HERE.parents[0].name == "modulos":
        candidate = HERE.parents[1]
    if candidate and candidate.exists() and looks_like_project(candidate):
        return candidate
    if not interactive:
        log("Não foi possível detectar a raiz do projeto. Use --project.", "error")
        sys.exit(1)
    while True:
        value = prompt_input("Informe a raiz do projeto alvo")
        if not value:
            continue
        path = Path(value).expanduser().resolve()
        if path.exists() or allow_create:
            path.mkdir(parents=True, exist_ok=True)
            return path
        log("Caminho inválido.", "warn")


def slugify(value: str, default: str = "app") -> str:
    if not value:
        return default
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or default


def find_package_root() -> Path:
    for parent in [HERE, *HERE.parents]:
        if (parent / PROJECT_TEMPLATE_DIRNAME).exists():
            return parent
        if (parent / "instalador").exists() and (parent / "modulos").exists():
            return parent
    return HERE.parents[1]


def is_dir_empty(path: Path) -> bool:
    return not any(path.iterdir())


def render_template_tree(
    src: Path,
    dest: Path,
    replacements: dict[str, str],
    force: bool = False,
    interactive: bool = True,
) -> list[str]:
    touched: list[str] = []
    for path in src.rglob("*"):
        if "__pycache__" in path.parts or path.name.endswith(".pyc") or path.name == ".DS_Store":
            continue
        rel = path.relative_to(src)
        target = dest / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not force:
            if interactive and not prompt_yes_no(f"Sobrescrever {target}?", False):
                continue
        try:
            content = path.read_text("utf-8")
            for key, value in replacements.items():
                content = content.replace(key, value)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, "utf-8")
        except UnicodeDecodeError:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        touched.append(str(target))
    return touched


def copy_tree(src: Path, dest: Path, force: bool = False) -> None:
    if not src.exists():
        return
    if dest.exists() and not force:
        return
    shutil.copytree(src, dest, dirs_exist_ok=force)


def bootstrap_project(
    manifest: dict,
    project_root: Path,
    interactive: bool,
    force: bool,
    project_name: str | None,
    port_override: int | None,
) -> dict:
    package_root = find_package_root()
    template_root = package_root / PROJECT_TEMPLATE_DIRNAME
    if not template_root.exists():
        log("Template de projeto não encontrado no pacote.", "error")
        sys.exit(1)

    if project_root.exists() and not is_dir_empty(project_root) and not force:
        if interactive:
            if not prompt_yes_no("A pasta do projeto não está vazia. Continuar?", False):
                sys.exit(1)
        else:
            log("Projeto não está vazio. Use --force para sobrescrever.", "error")
            sys.exit(1)

    app_meta = manifest.get("app", {})
    project_name = project_name or app_meta.get("name") or "Projeto"
    project_slug = slugify(project_name)
    app_id = app_meta.get("id") or 0
    try:
        app_id_int = int(app_id)
    except Exception:
        app_id_int = 0
    port = port_override or (11000 + app_id_int if app_id_int else 11000)

    replacements = {
        "ix.BZP-DealScore-UTM-Sync": project_name,
        "ix-bzp-dealscore-utm-sync": project_slug,
        "ix.BZP-DealScore-UTM-Sync": app_meta.get("name") or project_name,
        "11": str(app_id),
        "11011": str(port),
        "mopgled-T.1": app_meta.get("theme_id") or "",
        "single": app_meta.get("mode") or "",
        "http://ix-renomeie.onrender.com/mopgled/apps/11/css": manifest.get("cdn", {}).get("css_url") or "",
        "http://ix-renomeie.onrender.com/mopgled/apps/11/js": manifest.get("cdn", {}).get("js_url") or "",
        "http://ix-renomeie.onrender.com/mopgled/apps/11/module": manifest.get("cdn", {}).get("module_url") or "",
        "http://ix-renomeie.onrender.com/mopgled": manifest.get("service", {}).get("api_base") or "",
        "2026-02-11T15:16:37.996693": manifest.get("generated_at") or datetime.utcnow().isoformat(),
        "141ec870c90d0fb985da18b23727440fd6a13ef7": manifest.get("auth", {}).get("sync_token") or "",
    }

    touched = render_template_tree(template_root, project_root, replacements, force=force, interactive=interactive)
    log(f"Bootstrap aplicado em {project_root} ({len(touched)} arquivos).", "success")

    package_mod = package_root / "modulos" / "mopgled-client"
    target_mod = project_root / "modulos" / "mopgled-client"
    if package_mod.exists():
        target_mod.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(package_mod, target_mod, dirs_exist_ok=True)
        log("mopgled-client copiado para /modulos.", "success")

    docs_mopgled = project_root / "_docs" / "mopgled"
    docs_mopgled.mkdir(parents=True, exist_ok=True)
    for doc_name in ("README.md", "AGENT.md"):
        src_doc = package_root / doc_name
        if src_doc.exists():
            shutil.copy2(src_doc, docs_mopgled / doc_name)
    inst_dir = package_root / "instalador"
    if inst_dir.exists():
        shutil.copytree(inst_dir, docs_mopgled / "instalador", dirs_exist_ok=True)
        log("Instalador copiado para /_docs/mopgled.", "success")

    return replacements


def has_templates(dir_path: Path) -> bool:
    patterns = ["*.html", "*.htm", "*.jinja", "*.jinja2", "*.tmpl"]
    for pattern in patterns:
        if any(dir_path.rglob(pattern)):
            return True
    return False


def discover_template_dirs(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for rel in COMMON_TEMPLATE_DIRS:
        path = project_root / rel
        if path.exists() and has_templates(path):
            candidates.append(path)
    if candidates:
        return candidates
    for path in project_root.rglob("*"):
        if not path.is_dir():
            continue
        if any(part in SKIP_SCAN_DIRS for part in path.parts):
            continue
        if has_templates(path):
            candidates.append(path)
        if len(candidates) >= 5:
            break
    return candidates


def normalize_dirs(project_root: Path, dirs: list[str]) -> list[Path]:
    results = []
    for value in dirs:
        raw = value.strip()
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path
        results.append(path.resolve())
    return results


def select_template_dirs(
    project_root: Path,
    manifest: dict,
    explicit_dirs: list[str],
    interactive: bool,
) -> list[Path]:
    if explicit_dirs:
        return normalize_dirs(project_root, explicit_dirs)
    defaults = manifest.get("defaults", {})
    default_dir = defaults.get("templates_dir")
    if default_dir:
        candidate = project_root / default_dir
        if candidate.exists() and has_templates(candidate):
            return [candidate]
    candidates = discover_template_dirs(project_root)
    if not candidates:
        return []
    if len(candidates) == 1 or not interactive:
        return [candidates[0]]
    options = [str(path) for path in candidates]
    choice = prompt_choice("Foram encontrados múltiplos diretórios de template.", options, 0)
    return [candidates[choice]]


def find_candidate_templates(templates_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in CANDIDATE_PATTERNS:
        path = templates_dir / pattern
        if path.exists():
            candidates.append(path)
    if candidates:
        return candidates
    for path in templates_dir.rglob("*.html"):
        try:
            text = path.read_text("utf-8")
        except Exception:
            continue
        if "</head>" in text.lower() and "</body>" in text.lower():
            candidates.append(path)
        if len(candidates) >= 5:
            break
    return candidates


def infer_inject_mode(mode: str, template_file: Path | None) -> str:
    if mode in {"include", "raw"}:
        return mode
    if not template_file:
        return "include"
    try:
        text = template_file.read_text("utf-8")
    except Exception:
        return "include"
    if "{%" in text or "{{" in text:
        return "include"
    return "raw"


def build_raw_snippets(cdn_meta: dict) -> tuple[str, str]:
    css_url = cdn_meta.get("css_url") or ""
    js_url = cdn_meta.get("js_url") or ""
    head = "\n".join([
        "<!-- MopGled head include -->",
        f"<link rel=\"stylesheet\" href=\"{css_url}\">",
    ])
    scripts = "\n".join([
        "<!-- MopGled scripts include -->",
        f"<script type=\"module\" src=\"{js_url}\"></script>",
    ])
    return head, scripts


def template_has_markers(content_lower: str, markers: list[str]) -> bool:
    return any(marker in content_lower for marker in markers)


def insert_snippet(content: str, snippet: str, closing_tag: str) -> tuple[str, bool]:
    if snippet in content:
        return content, False
    lower = content.lower()
    idx = lower.rfind(closing_tag)
    if idx == -1:
        return content, False
    return content[:idx] + snippet + "\n" + content[idx:], True


def create_backup_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def backup_file(path: Path, backup_root: Path, tracked: set[Path], project_root: Path) -> None:
    if path in tracked or not path.exists():
        return
    try:
        rel = path.relative_to(project_root)
    except ValueError:
        return
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    tracked.add(path)


def restore_backup(timestamp: str, project_root: Path) -> None:
    backup_path = BACKUP_DIR / timestamp
    if not backup_path.exists():
        log(f"Backup {timestamp} não encontrado.", "error")
        sys.exit(1)
    for item in backup_path.rglob("*"):
        if item.is_dir():
            continue
        target = project_root / item.relative_to(backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
    log(f"Backup {timestamp} restaurado com sucesso.", "success")


def copy_asset(
    asset_name: str,
    target: Path,
    touched: list[str],
    backup_root: Path,
    backed_up: set[Path],
    project_root: Path,
) -> None:
    source = ASSETS_DIR / asset_name
    target.parent.mkdir(parents=True, exist_ok=True)
    backup_file(target, backup_root, backed_up, project_root)
    shutil.copy2(source, target)
    touched.append(str(target.relative_to(project_root)))
    log(f"Copiado {asset_name} -> {target}", "success")


def patch_template(
    file_path: Path,
    head_snippet: str,
    script_snippet: str,
    backup_root: Path,
    backed_up: set[Path],
    touched: list[str],
    project_root: Path,
) -> tuple[bool, bool]:
    if not file_path.exists():
        return False, False
    original = file_path.read_text("utf-8")
    lower = original.lower()
    head_present = head_snippet.lower() in lower or template_has_markers(
        lower, ["mopgled/head_include.html", "mopgled.css"]
    )
    body_present = script_snippet.lower() in lower or template_has_markers(
        lower, ["mopgled/scripts_include.html", "mopgled.js"]
    )
    if head_present and body_present:
        log(f"Template {file_path} já contém MopGled. Pulando injeção.", "info")
        return False, True
    updated = original
    head_changed = False
    body_changed = False
    if not head_present:
        updated, head_changed = insert_snippet(updated, f"{head_snippet}\n", "</head>")
    if not body_present:
        updated, body_changed = insert_snippet(updated, f"{script_snippet}\n", "</body>")
    if head_changed or body_changed:
        backup_file(file_path, backup_root, backed_up, project_root)
        file_path.write_text(updated, "utf-8")
        touched.append(str(file_path.relative_to(project_root)))
        log(f"Atualizado template {file_path}", "success")
        return True, False
    log(f"Nada para ajustar em {file_path} (snippets já presentes ou sem <head>/<body>).", "info")
    return False, False


def dump_report(
    project_root: Path,
    templates_dirs: list[Path],
    touched: list[str],
    patched: list[str],
    preconfigured: list[str],
    assets: list[str],
    status_code: str,
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "project_root": str(project_root),
        "templates_dirs": [str(p) for p in templates_dirs],
        "files": touched,
        "patched_templates": patched,
        "preconfigured_templates": preconfigured,
        "assets_written": assets,
        "status_code": status_code,
    }
    (LOGS_DIR / "last-run.log").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        "utf-8",
    )
    log(f"Relatório salvo em {LOGS_DIR / 'last-run.log'}", "success")


def build_status_code(payload: dict, token: str | None) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if token:
        signature = hmac.new(token.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
        return f"{encoded}.{signature}"
    return encoded


def decode_status_code(code_line: str, token: str | None) -> tuple[dict | None, bool]:
    raw = code_line.strip()
    match = re.search(r"MopGled\s*-\s*OK\s*-\s*([A-Za-z0-9_.-]+)", raw)
    if match:
        raw = match.group(1)
    if not raw:
        return None, False
    if "." in raw:
        encoded, signature = raw.split(".", 1)
    else:
        encoded, signature = raw, ""
    padded = encoded + "=" * (-len(encoded) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except Exception:
        return None, False
    if token and signature:
        expected = hmac.new(token.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
        return payload, signature == expected
    return payload, False


def token_from_manifest(manifest: dict) -> str | None:
    auth = manifest.get("auth", {}) if isinstance(manifest, dict) else {}
    token = auth.get("sync_token") or manifest.get("sync_token")
    if not token:
        return None
    normalized = str(token).strip()
    return normalized or None


def resolve_sync_token(project_root: Path, token_arg: str | None, manifest: dict) -> str | None:
    if token_arg:
        return token_arg.strip()
    token = os.getenv("MOPGLED_SYNC_TOKEN") or os.getenv("ALIXIA_SYNC_TOKEN")
    if token:
        return token.strip()
    for filename in DOTENV_FILES:
        env_path = project_root / filename
        env_data = read_dotenv(env_path)
        token = env_data.get("MOPGLED_SYNC_TOKEN") or env_data.get("ALIXIA_SYNC_TOKEN")
        if token:
            return token.strip()
    return token_from_manifest(manifest)


def ensure_latest_package(
    manifest: dict,
    token: str | None,
    interactive: bool,
    project_root: Path,
    save_token: bool,
) -> tuple[dict, str | None]:
    module_url = manifest.get("cdn", {}).get("module_url")
    current_ts = parse_ts(manifest.get("generated_at"))
    if not module_url:
        return manifest, token

    def attempt_fetch(sync_token: str | None) -> bytes:
        headers = {"User-Agent": "MopGledInstaller/2.0"}
        if sync_token:
            headers["Authorization"] = f"Bearer {sync_token}"
        req = Request(module_url, headers=headers)
        with urlopen(req, timeout=12) as resp:  # nosec - endpoint controlado
            return resp.read()

    while True:
        try:
            data = attempt_fetch(token)
        except HTTPError as exc:
            if exc.code == 401:
                log("Atualização bloqueada (401). Token ausente ou inválido.", "warn")
                if interactive:
                    new_token = prompt_input("Cole o token Bearer (ou Enter para pular)")
                    if new_token:
                        token = new_token.strip()
                        if save_token:
                            write_dotenv(project_root / ".env", "MOPGLED_SYNC_TOKEN", token)
                            log("Token salvo em .env", "success")
                        continue
                return manifest, token
            log(f"Não foi possível verificar atualizações do módulo ({exc}).", "warn")
            return manifest, token
        except URLError as exc:
            log(f"Não foi possível verificar atualizações do módulo ({exc}).", "warn")
            return manifest, token

        with tempfile.TemporaryDirectory() as tmp_dir:
            archive = Path(tmp_dir) / "module.zip"
            archive.write_bytes(data)
            with zipfile.ZipFile(archive) as zf:
                manifest_member = next(
                    (
                        name
                        for name in zf.namelist()
                        if name.endswith("modulos/mopgled-client/manifests/mopgled.json")
                    ),
                    None,
                )
                if not manifest_member:
                    log("Pacote remoto não contém mopgled-client. Ignorando atualização.", "warn")
                    return manifest, token
                remote_manifest = json.loads(zf.read(manifest_member).decode("utf-8"))
                remote_ts = parse_ts(remote_manifest.get("generated_at"))
                if current_ts and remote_ts and remote_ts <= current_ts:
                    return manifest, token
                zf.extractall(Path(tmp_dir) / "pkg")
                extracted_root = next(Path(tmp_dir, "pkg").glob("*/modulos/mopgled-client"), None)
                if not extracted_root:
                    candidate = Path(tmp_dir, "pkg") / "modulos" / "mopgled-client"
                    extracted_root = candidate if candidate.exists() else None
                if not extracted_root:
                    log("Pacote remoto não contém modulos/mopgled-client, ignorando.", "warn")
                    return manifest, token
                log("Atualização do MopGled Client encontrada. Aplicando novo pacote...", "info")
                for item in extracted_root.rglob("*"):
                    rel = item.relative_to(extracted_root)
                    dest = HERE / rel
                    if item.is_dir():
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest)
                log("Pacote atualizado. Prosseguindo com a instalação...", "success")
                return load_manifest(), token


def apply_installation(
    manifest: dict,
    project_root: Path,
    templates_dirs: list[Path],
    inject_mode: str,
) -> tuple[list[str], list[str], list[str], list[str], Path]:
    app_meta = manifest.get("app", {})
    cdn_meta = manifest.get("cdn", {})

    log(f"Projeto: {project_root}", "info")
    log(f"Templates alvo: {[str(p) for p in templates_dirs]}", "info")
    log(
        f"APP: {app_meta.get('name')} (ID {app_meta.get('id')}) – Tema {app_meta.get('theme_id')} [{app_meta.get('mode')}]",
        "info",
    )
    log(f"CSS: {cdn_meta.get('css_url')}", "info")
    log(f"JS : {cdn_meta.get('js_url')}", "info")

    touched: list[str] = []
    patched: list[str] = []
    preconfigured: list[str] = []
    assets_written: list[str] = []
    backup_root = create_backup_dir()
    backed_up: set[Path] = set()

    if inject_mode == "include" and templates_dirs:
        for base_templates_dir in templates_dirs:
            targets = [
                ("mopgled_head.html", base_templates_dir / TEMPLATE_NAMESPACE / "head_include.html"),
                ("mopgled_scripts.html", base_templates_dir / TEMPLATE_NAMESPACE / "scripts_include.html"),
            ]
            for asset_name, dest in targets:
                copy_asset(asset_name, dest, touched, backup_root, backed_up, project_root)
                assets_written.append(str(dest.relative_to(project_root)))

    head_snippet = HEAD_SNIPPET_INCLUDE
    script_snippet = SCRIPTS_SNIPPET_INCLUDE
    if inject_mode == "raw":
        head_snippet, script_snippet = build_raw_snippets(cdn_meta)

    template_files: list[Path] = []
    for templates_dir in templates_dirs:
        template_files.extend(find_candidate_templates(templates_dir))

    template_files = list(dict.fromkeys(template_files))

    if not template_files:
        log("Nenhum template base encontrado para aplicar os includes.", "warn")
        return touched, patched, assets_written, backup_root

    for template_file in template_files:
        changed, already = patch_template(
            template_file,
            head_snippet,
            script_snippet,
            backup_root,
            backed_up,
            touched,
            project_root,
        )
        if changed:
            patched.append(str(template_file.relative_to(project_root)))
        elif already:
            preconfigured.append(str(template_file.relative_to(project_root)))

    return touched, patched, preconfigured, assets_written, backup_root


def post_install_check(status_code: str, token: str | None) -> None:
    if not prompt_yes_no("Deseja executar o checklist rapido agora?", False):
        return
    layout_ok = prompt_yes_no("O layout foi alterado conforme esperado?", False)
    code_line = prompt_input("Cole a linha 'MopGled - OK - ...' (ou Enter para pular)")
    if code_line:
        payload, verified = decode_status_code(code_line, token)
        if payload:
            log(f"Codigo decodificado: {json.dumps(payload, ensure_ascii=False)}", "info")
            warnings = payload.get("warnings") if isinstance(payload, dict) else None
            if warnings:
                log(f"Avisos detectados: {', '.join(warnings)}", "warn")
                if "templates_not_found" in warnings:
                    log("Sugestao: use --inject-mode raw ou inclua manualmente os snippets em seu HTML base.", "warn")
            if verified:
                log("Assinatura conferida com sucesso.", "success")
            else:
                log("Assinatura nao validada (token ausente ou divergente).", "warn")
        else:
            log("Nao foi possivel decodificar o codigo.", "warn")
    if not layout_ok:
        log("Sugestao: valide se o template base recebeu os includes e se o dominio esta autorizado.", "warn")


def cleanup_prompt(backup_root: Path) -> None:
    options = [
        "Apagar backups e logs",
        "Apagar apenas logs e manter comando de restore",
        "Nao fazer nada",
    ]
    choice = prompt_choice("Limpeza pos-instalacao:", options, 2)
    if choice == 0:
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
        shutil.rmtree(LOGS_DIR, ignore_errors=True)
        log("Backups e logs removidos.", "success")
    elif choice == 1:
        shutil.rmtree(LOGS_DIR, ignore_errors=True)
        restore_cmd = f"python3 modulos/mopgled-client/instalar.py --restore {backup_root.name}"
        (HERE / "RESTORE_MOPGLED.txt").write_text(restore_cmd + "\n", "utf-8")
        log("Logs removidos. Comando de restore salvo em RESTORE_MOPGLED.txt", "success")


def main() -> None:
    parser = argparse.ArgumentParser(description="Instalador do MopGled Client.")
    parser.add_argument("--project", help="Raiz do projeto alvo.")
    parser.add_argument("--templates-dir", action="append", help="Diretorio de templates (relativo ao projeto).")
    parser.add_argument("--inject-mode", choices=["auto", "include", "raw"], default="auto")
    parser.add_argument("--token", help="Token Bearer para sincronizacao do pacote.")
    parser.add_argument("--save-token", action="store_true", help="Salvar token em .env do projeto.")
    parser.add_argument("--skip-update", action="store_true", help="Ignorar verificacao de atualizacoes do pacote.")
    parser.add_argument("--restore", metavar="YYYYMMDD_HHMMSS", help="Restaura um backup gerado previamente.")
    parser.add_argument("--verify", help="Decodifica um codigo MopGled.")
    parser.add_argument("--bootstrap", action="store_true", help="Cria estrutura inicial do projeto.")
    parser.add_argument("--bootstrap-only", action="store_true", help="Somente bootstrap (sem instalar MopGled).")
    parser.add_argument("--force", action="store_true", help="Sobrescrever arquivos existentes no bootstrap.")
    parser.add_argument("--project-name", help="Nome do projeto (bootstrap).")
    parser.add_argument("--port", type=int, help="Porta local do app (bootstrap).")
    parser.add_argument("--non-interactive", action="store_true", help="Nao solicitar entradas interativas.")
    args = parser.parse_args()

    if args.bootstrap_only and not args.bootstrap:
        args.bootstrap = True

    interactive = sys.stdin.isatty() and not args.non_interactive
    prune_old_backups()
    manifest = load_manifest()

    if args.verify:
        project_root = Path(args.project).expanduser().resolve() if args.project else Path.cwd()
        token = resolve_sync_token(project_root, args.token, manifest)
        payload, verified = decode_status_code(args.verify, token)
        if not payload:
            log("Codigo invalido ou nao decodificavel.", "error")
            sys.exit(1)
        log(f"Codigo decodificado: {json.dumps(payload, ensure_ascii=False)}", "info")
        if verified:
            log("Assinatura conferida com sucesso.", "success")
        else:
            log("Assinatura nao validada (token ausente ou divergente).", "warn")
        return

    project_root = resolve_project_root(args.project, interactive, allow_create=args.bootstrap)

    if not args.bootstrap and interactive and not looks_like_project(project_root):
        default_bootstrap = is_dir_empty(project_root)
        if prompt_yes_no("Projeto parece novo. Deseja aplicar o bootstrap agora?", default_bootstrap):
            args.bootstrap = True

    if args.bootstrap:
        bootstrap_project(
            manifest,
            project_root,
            interactive,
            args.force,
            args.project_name,
            args.port,
        )
        if args.bootstrap_only:
            return

    if args.restore:
        restore_backup(args.restore, project_root)
        return

    token = resolve_sync_token(project_root, args.token, manifest)
    if args.save_token and token:
        write_dotenv(project_root / ".env", "MOPGLED_SYNC_TOKEN", token)
        log("Token salvo em .env", "success")

    if not args.skip_update:
        manifest, token = ensure_latest_package(manifest, token, interactive, project_root, args.save_token)

    templates_dirs = select_template_dirs(project_root, manifest, args.templates_dir or [], interactive)
    if not templates_dirs:
        log("Diretorio de templates nao encontrado.", "warn")
        if interactive:
            choice = prompt_choice(
                "Como deseja prosseguir?",
                [
                    "Criar base.html em um novo diretorio de templates",
                    "Informar um diretorio de templates manualmente",
                    "Pular injeção automatica",
                    "Cancelar instalacao",
                ],
                2,
            )
            if choice == 0:
                base_dir = prompt_input("Diretorio de templates", "templates")
                base_name = prompt_input("Nome do template base", "base.html")
                target_dir = (project_root / base_dir).resolve()
                target_dir.mkdir(parents=True, exist_ok=True)
                head_snippet = HEAD_SNIPPET_INCLUDE
                script_snippet = SCRIPTS_SNIPPET_INCLUDE
                inject_mode = infer_inject_mode(args.inject_mode, None)
                if inject_mode == "raw":
                    head_snippet, script_snippet = build_raw_snippets(manifest.get("cdn", {}))
                base_path = target_dir / base_name
                if not base_path.exists() or prompt_yes_no("Template ja existe. Sobrescrever?", False):
                    html = "\n".join([
                        "<!doctype html>",
                        "<html lang=\"pt-br\">",
                        "<head>",
                        "  <meta charset=\"utf-8\">",
                        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
                        f"  {head_snippet}",
                        "</head>",
                        "<body>",
                        "  <!-- Conteudo do app -->",
                        f"  {script_snippet}",
                        "</body>",
                        "</html>",
                    ])
                    base_path.write_text(html + "\n", "utf-8")
                    log(f"Template criado em {base_path}", "success")
                templates_dirs = [target_dir]
            elif choice == 1:
                manual_dir = prompt_input("Diretorio de templates")
                if manual_dir:
                    templates_dirs = [Path(manual_dir).expanduser().resolve()]
            elif choice == 2:
                templates_dirs = []
            else:
                log("Instalacao cancelada pelo usuario.", "warn")
                sys.exit(1)

    template_sample = None
    if templates_dirs:
        candidates = find_candidate_templates(templates_dirs[0])
        template_sample = candidates[0] if candidates else None

    inject_mode = infer_inject_mode(args.inject_mode, template_sample)

    touched, patched, preconfigured, assets_written, backup_root = apply_installation(
        manifest,
        project_root,
        templates_dirs,
        inject_mode,
    )

    warnings: list[str] = []
    if not templates_dirs:
        warnings.append("templates_not_found")
    if templates_dirs and not patched and not preconfigured:
        warnings.append("templates_not_patched")

    status_payload = {
        "app_id": manifest.get("app", {}).get("id"),
        "app_name": manifest.get("app", {}).get("name"),
        "module": "mopgled-client",
        "generated_at": manifest.get("generated_at"),
        "installed_at": datetime.utcnow().isoformat(),
        "project_root": str(project_root),
        "files": touched,
        "patched": patched,
        "preconfigured": preconfigured,
        "assets_written": assets_written,
        "templates_dirs": [str(p) for p in templates_dirs],
        "inject_mode": inject_mode,
        "warnings": warnings,
    }
    status_code = build_status_code(status_payload, token)

    dump_report(project_root, templates_dirs, touched, patched, preconfigured, assets_written, status_code)

    log("Instalacao do MopGled Client concluida. Abra o app e valide o layout.", "success")
    log(f"MopGled - OK - {status_code}", "success")
    log(f"Se precisar restaurar, rode: python3 modulos/mopgled-client/instalar.py --restore {backup_root.name}", "info")

    if interactive:
        post_install_check(status_code, token)
        cleanup_prompt(backup_root)


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
