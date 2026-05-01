---
applyTo: '.env.wp'
ixwp:
  layer: heavy
  module: notifications
  weight: 480
  since: 2.0.0
  breaking: false
  requires: [core]
---

<!-- ix.WP V2.0.0 — Pushover notifications (heavy, opt-in only) -->

# ix.WP — Notificações Push (Pushover)

Ativado quando: `PUSHOVER_STATUS=ON` em `.env.wp`

## Matriz de Notificação (12 Níveis)

| Nível | Evento | Prioridade | Som |
|-------|--------|------------|-----|
| 1 | 🚀 Início | -1 (Low) | `cosmic` |
| 2 | ⏳ Andamento | -1 (Low) | `gamelan` |
| 3 | ✅ Etapa concluída | 0 (Normal) | `magic` |
| 4 | 🎉 Sucesso final | 0 (Normal) | `pianobar` |
| 5 | ⚠️ Falha remediável | 0 (Normal) | `falling` |
| 6 | 🔍 Solução aferida | 0 (Normal) | `incoming` |
| 7 | 🔨 Implementada | 0 (Normal) | `mechanical` |
| 8 | 🔔 Alerta simples | 0 (Normal) | `cashregister` |
| 9 | ⚠️ Alerta médio | 1 (High) | `climb` |
| 10 | 🔴 Alerta alto | 1 (High) | `siren` |
| 11 | 🚨 Catástrofe | 2 (Emergency) | `spacealarm` |
| 12 | 💀 Crítico | 2 (Emergency) | `alien` |

## Comando
```bash
python3 _docs/ix.WP-V{VERSION}/1-modulos/6-Pushover/notify.py \
  "Título" "<b>Status:</b> msg" --level 3
```

## Limites
- Body: 1024 chars | Title: 250 chars
- HTML: `<b>`, `<i>`, `<u>`, `<font>`, `<a>`, `<br>`

> Para detalhes: `#ix-wp-pushover`
