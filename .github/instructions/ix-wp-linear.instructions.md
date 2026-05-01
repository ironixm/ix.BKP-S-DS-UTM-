---
applyTo: 'JOBS.md,JOBS.db,.env.wp,SONHOS.md'
ixwp:
  layer: domain
  module: linear
  weight: 520
  since: 2.0.0
  breaking: false
  requires: [core]
---

<!-- ix.WP V2.0.0 — Linear tracking (domain, loaded on task-related files) -->

# ix.WP — Issue-Tracking (Linear)

## Workflow
1. **Criar issue** no Linear com título descritivo
2. **Executar** a tarefa
3. **Documentar Activities** — comentários incrementais
4. **Comentário final** com resolução técnica
5. **Fechar** se resolvida

## Activity Format
```markdown
### 🕐 [HH:MM] Activity #N
👤 Usuário: [resumo]
🤖 Agent: [ação]
📎 Resultado: [decisão]
```

## Comandos
```bash
source .env && python3 _docs/ix.WP-V{VERSION}/1-modulos/2-Linear/linear_sync.py create \
  --title "Título" --description "Descrição"
source .env && python3 _docs/ix.WP-V{VERSION}/1-modulos/2-Linear/linear_sync.py comment \
  --issue "FVR-XXX" --body "### 🕐 HH:MM Activity #N ..."
```

## JOBS.md
- Espelho visual das tarefas Linear (rolling 7 dias)
- Agents DEVEM consultar JOBS.md para contexto de tarefas pendentes

> Para detalhes completos: `#ix-wp-linear`
