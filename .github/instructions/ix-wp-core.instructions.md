---
applyTo: '**'
ixwp:
  layer: core
  module: core
  weight: 380
  since: 2.0.0
  breaking: false
  requires: []
---

<!-- ix.WP V2.0.0 — Core instruction (always-on, lightweight) -->

# ix.WP — Core

## Idioma e Tom
- **Idioma:** PT-BR para comunicação; termos técnicos em inglês
- **Tom:** Executivo, técnico, direto. Sem narrativas longas.
- **Outputs:** Tabelas, seções, Mermaid quando necessário.

## Timezone
Todo horário: `America/Sao_Paulo`.
```bash
TZ='America/Sao_Paulo' date '+%Y-%m-%d %H:%M'
```

## Diretório Temporário
**NUNCA** `/tmp/` do sistema. Sempre `./tmp/` do projeto (gitignored).

## Sessão
Nome: `ix.{Projeto}-V{Versão}|{Feature}|{DDMMYY}-{HHMM}`
Ler `.env.wp` no início de cada sessão.

## Finalização
Antes de encerrar, 1 parágrafo com: (1) o que foi feito, (2) decisões pendentes, (3) próximos passos.

## Profile
Consultar `ix-wp.profile.json` para módulos ativos.
Instruções modulares em `.github/instructions/`.
