---
applyTo: '.github/**,.gitmessage,CHANGELOG.md'
ixwp:
  layer: domain
  module: git
  weight: 350
  since: 2.0.0
  breaking: false
  requires: [core]
---

<!-- ix.WP V2.0.0 — Git conventions (domain, loaded on git-related files) -->

# ix.WP — Git Conventions

## Commits
**Formato:** `Vx.y.z - ModuloX|ModuloY - Título - TIPO - DDMMYYHHMM`

| Tipo | Descrição |
|------|-----------|
| FEAT | Nova funcionalidade |
| FIX | Correção de bug |
| DOCS | Documentação |
| REFACTOR | Refatoração |
| TEST | Testes |
| CHORE | Manutenção |

## Branches
- Feature: `feature/{prefixo}-###-{descricao}`
- BRISA: `brisa/{YYYY-MM-DD}-{HHmm}-{topico}`

## MODO_GIT
Configurável via `.env.wp`:
- `ALWAYS` — commit/push a cada resposta
- `<N>` — a cada N minutos
- `DEMAND` — somente quando solicitado
- `BCE` — antes de eventos críticos
