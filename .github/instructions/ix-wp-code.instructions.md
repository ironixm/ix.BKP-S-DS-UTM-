---
applyTo: 'src/**,*.ts,*.py,*.sh,*.js,*.css'
ixwp:
  layer: domain
  module: code
  weight: 320
  since: 2.0.0
  breaking: false
  requires: [core]
---

<!-- ix.WP V2.0.0 — Code conventions (domain, loaded on source files) -->

# ix.WP — Code Conventions

## Naming
- **camelCase** para funções/variáveis
- **PascalCase** para classes/interfaces
- **UPPER_SNAKE** para constantes

## Segredos
- `.env` / `.env.wp` — Credenciais (NUNCA versionadas)
- `.env.example` — Template com placeholders (versionado)
