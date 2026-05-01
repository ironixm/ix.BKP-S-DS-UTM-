---
applyTo: '.env.wp'
ixwp:
  layer: heavy
  module: automato
  weight: 350
  since: 2.0.0
  breaking: false
  requires: [core, notifications]
---

<!-- ix.WP V2.0.0 — AUTOMATO mode (heavy, opt-in only) -->

# ix.WP — Modo Autônomo (AUTOMATO)

Ativado quando: `AUTOMATO=ON` em `.env.wp`

## Estado do Agent
Ler `.env.wp` no início. Default se ausente: `AUTOMATO=OFF`, `PUSHOVER_STATUS=OFF`, `MODO_GIT=BCE`.

## Comandos
| Comando | Ação |
|---------|------|
| `/automato=on` | `AUTOMATO=ON` + `PUSHOVER_STATUS=ON` |
| `/automato=off` | `AUTOMATO=OFF` |
| `/pushover=on/off` | Controla notificações |
| `/git=<modo>` | `MODO_GIT=<modo>` |

## Fluxo (AUTOMATO=ON)
1. Ler `.env.wp` → verificar AUTOMATO
2. Prioridade: Todo List → JOBS.md → JOBS.db → Sonhos → /_docs/
3. Notificar a cada conclusão (via notify.py)
4. Commits conforme MODO_GIT
5. AUTOMATO=ON SEMPRE força PUSHOVER_STATUS=ON
