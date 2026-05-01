#!/usr/bin/env node
/* # ╔═════════════════════════════════════════════════════════════════╗ */
/* # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ */
/* # ║  ▄█▛▘‾ ‾▝▜█▄  │ Install Node – V1.0.0                          │║ */
/* # ║ ██▘       ▝██ │                                                │║ */
/* # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ */
/* # ║ ███▄_   _▄███ │ By Ir.On                                       │║ */
/* # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ */
/* # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║ */
/* # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ */
/* # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ */
/* # ║      ██    ▜▛ │ Caminho:                                       │║ */
/* # ║      ▜▛       │ _docs/mopgled/instalador/install-node.js       │║ */
/* # ║               ├────────────────────────────────────────────────┤║ */
/* # ║               │ Detalhes:                                      │║ */
/* # ║               │ * V1.0.0 - [sem detalhes]                      │║ */
/* # ║               │                                                │║ */
/* # ║               └────────────────────────────────────────────────┘║ */
/* # ╚═════════════════════════════════════════════════════════════════╝ */

// Wrapper do instalador MopGled Client (Node)

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const root = path.resolve(__dirname, "..");
const installer = path.join(root, "modulos", "mopgled-client", "instalar.py");

if (!fs.existsSync(installer)) {
  console.error("[ERRO] instalador não encontrado em", installer);
  process.exit(1);
}

const args = [installer, ...process.argv.slice(2)];
const candidates = ["python3", "python", "py"];

for (const bin of candidates) {
  const result = spawnSync(bin, args, { stdio: "inherit" });
  if (result.status === 0) {
    process.exit(0);
  }
  if (result.error && result.error.code === "ENOENT") {
    continue;
  }
  if (result.status != null) {
    process.exit(result.status);
  }
}

console.error("[ERRO] Python não encontrado. Instale o Python 3 ou rode o instalador manualmente.");
process.exit(1);

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
