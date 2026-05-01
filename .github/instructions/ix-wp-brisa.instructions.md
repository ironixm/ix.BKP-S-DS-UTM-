---
applyTo: '.env.wp'
ixwp:
  layer: heavy
  module: brisa
  weight: 580
  since: 2.0.0
  breaking: false
  requires: [core, notifications]
---

<!-- ix.WP V2.0.0 — BRISA mode (heavy, opt-in only) -->

# ix.WP — BRISA (Modo Autônomo Contínuo)

**BRISA = Base de Refino Incremental, Simulação e Aprendizado.**
Operador liga e sai. Agent trabalha até o tempo acabar.

Ativado quando: `BRISA=ON` em `.env.wp`

## Reconhecimento Imediato
Ativar ao receber: `/brisa=on`, `brisa=on`, `ligar brisa`, `ativar brisa`
NÃO pesquisar o que é BRISA. NÃO pedir confirmações (exceto duração).

## Ativação — 9 passos
1. Setar `.env.wp`: BRISA=ON, AUTOMATO=ON, PUSHOVER_STATUS=ON
2. Confirmar horário (TZ=America/Sao_Paulo)
3. Extrair duração → perguntar UMA VEZ se não vier
4. Calcular BRISA_END_TIME
5. `mkdir -p tmp && caffeinate -i & && echo $! > tmp/brisa-caffeinate.pid`
6. Branch `brisa/<YYYY-MM-DD>-<HHmm>-<topico>` — git push -u
7. Ler tarefas: Todo List → JOBS.md → Linear
8. Criar `tmp/brisa-decisoes-pendentes.md`
9. notify.py "🌿 BRISA ON" --level 1

## Loop
```
ENQUANTO agora < BRISA_END_TIME E há tarefas:
  → microciclo → notificar --level 3 → próxima tarefa
SE sem tarefas → docs/JOBS/lc — NUNCA ocioso
AO END_TIME → Handoff
```

## Proibições
- Parar para perguntar
- Ficar ocioso
- Branch fora do padrão
- Trabalhar na main

## Handoff
Commit → lc-save → decisões pendentes → encerrar caffeinate → notify --level 4 → BRISA=OFF
