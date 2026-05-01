#!/usr/bin/env bash
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Autosync – V1.0.0                              │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:16         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/modulos/mopgled-client/autosy... │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

# AutoSync MopGled (curl + python3)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${MOPGLED_MANIFEST:-$ROOT/manifests/mopgled.json}"
STATIC_DIR="${TARGET_STATIC_DIR:-$ROOT/../../static}"
LOG_DIR="$ROOT/logs"
META="${MOPGLED_META:-$LOG_DIR/autosync.meta.json}"
TOKEN="${MOPGLED_SYNC_TOKEN:-${ALIXIA_SYNC_TOKEN:-}}"

mkdir -p "$LOG_DIR" "$STATIC_DIR"

readarray -t urls < <(MANIFEST="$MANIFEST" python3 - <<'PY'
import json, os
manifest_path = os.environ["MANIFEST"]
data = json.load(open(manifest_path, "r", encoding="utf-8"))
cdn = data.get("cdn", {})
print(cdn.get("css_url", ""))
print(cdn.get("js_url", ""))
auth = data.get("auth", {})
print(auth.get("sync_token", "") or "")
PY
)
CSS_URL="${urls[0]}"
JS_URL="${urls[1]}"
MANIFEST_TOKEN="${urls[2]}"
if [ -z "$TOKEN" ] && [ -n "$MANIFEST_TOKEN" ]; then
  TOKEN="$MANIFEST_TOKEN"
fi

if [ -z "$CSS_URL" ] || [ -z "$JS_URL" ]; then
  echo "❌ URLs ausentes no manifest ($MANIFEST)."
  exit 1
fi

meta() {
  python3 - "$META" "$1" "$2" <<'PY'
import json, sys, os, time
path, kind, etag = sys.argv[1:]
meta = {}
if os.path.exists(path):
    try:
        meta = json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        meta = {}
meta.setdefault(kind, {})
if etag:
    meta[kind]["etag"] = etag
meta[kind]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
}

fetch() {
  local kind="$1" url="$2" out="$3"
  local headers_file="$out.headers"
  local etag=""
  if [ -f "$META" ]; then
    etag="$(META_PATH="$META" KIND="$kind" python3 - <<'PY'
import json, os
path = os.environ.get("META_PATH")
kind = os.environ.get("KIND")
try:
    meta = json.load(open(path, "r", encoding="utf-8"))
    print(meta.get(kind, {}).get("etag", ""))
except Exception:
    print("")
PY
    )"
  fi

  local hdrs=(-H "User-Agent: MopGledAutoSync/1.0")
  [ -n "$TOKEN" ] && hdrs+=(-H "Authorization: Bearer $TOKEN")
  [ -n "$etag" ] && hdrs+=(-H "If-None-Match: $etag")

  http_code=$(META_PATH="$META" KIND="$kind" curl -fsS -w '%{http_code}' -D "$headers_file" -o "$out.tmp" "${hdrs[@]}" "$url" || true)
  if [ "$http_code" = "304" ]; then
    rm -f "$out.tmp" "$headers_file"
    echo "↔️  $kind sem mudanças (304)"
    return 1
  fi
  if [ "$http_code" != "200" ]; then
    rm -f "$out.tmp" "$headers_file"
    echo "❌ Falha $kind (HTTP $http_code)"
    return 2
  fi

  mv "$out.tmp" "$out"
  etag_new="$(grep -i '^etag:' "$headers_file" | awk '{print $2}' | tr -d '\r')"
  meta "$kind" "$etag_new"
  echo "✅ $kind atualizado -> $out (etag=$etag_new)"
}

fetch css "$CSS_URL" "$STATIC_DIR/mopgled.css" || true
fetch js  "$JS_URL"  "$STATIC_DIR/mopgled.js"  || true

:
<<'EOF'
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
EOF
