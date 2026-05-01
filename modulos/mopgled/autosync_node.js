#!/usr/bin/env node
/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Autosync Node – V1.0.0                         │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ modulos/mopgled/autosync_node.js               │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.0 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */

// AutoSync MopGled (Node 18+ com fetch nativo)

const fs = require("fs");
const path = require("path");

const manifestPath =
  process.env.MOPGLED_MANIFEST ||
  path.join(__dirname, "manifests", "mopgled.json");
const staticDir =
  process.env.TARGET_STATIC_DIR || path.join(__dirname, "../../static");
const metaPath =
  process.env.MOPGLED_META || path.join(__dirname, "logs", "autosync.meta.json");
const token =
  process.env.MOPGLED_SYNC_TOKEN || process.env.ALIXIA_SYNC_TOKEN || "";

const headersBase = { "User-Agent": "MopGledAutoSync/1.0" };
if (token) headersBase.Authorization = `Bearer ${token}`;

function loadJson(file, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (_) {
    return fallback;
  }
}

function saveMeta(meta) {
  fs.mkdirSync(path.dirname(metaPath), { recursive: true });
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), "utf8");
}

async function fetchKind(kind, url, outPath, meta) {
  if (!url) throw new Error(`URL ${kind} ausente no manifest.`);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const headers = { ...headersBase };
  const etag = meta[kind]?.etag;
  if (etag) headers["If-None-Match"] = etag;

  const resp = await fetch(url, { headers });
  if (resp.status === 304) {
    console.log(`↔️  ${kind} sem mudanças (304)`);
    return false;
  }
  if (!resp.ok) {
    throw new Error(`Falha ${kind}: HTTP ${resp.status}`);
  }

  const buf = Buffer.from(await resp.arrayBuffer());
  fs.writeFileSync(outPath, buf);
  const newEtag = resp.headers.get("etag") || "";
  meta[kind] = {
    etag: newEtag,
    updated_at: new Date().toISOString(),
  };
  console.log(`✅ ${kind} atualizado -> ${outPath} (etag=${newEtag})`);
  return true;
}

async function main() {
  const manifest = loadJson(manifestPath);
  if (!manifest) throw new Error(`Manifest não encontrado: ${manifestPath}`);
  const cdn = manifest.cdn || {};
  const meta = loadJson(metaPath, {});

  const targets = [
    { kind: "css", url: cdn.css_url, out: path.join(staticDir, "mopgled.css") },
    { kind: "js", url: cdn.js_url, out: path.join(staticDir, "mopgled.js") },
  ];

  for (const t of targets) {
    await fetchKind(t.kind, t.url, t.out, meta);
  }
  saveMeta(meta);
}

main().catch((err) => {
  console.error("❌ AutoSync MopGled falhou:", err.message);
  process.exit(1);
});

/*
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
*/
