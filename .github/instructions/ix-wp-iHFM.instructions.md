---
applyTo: 'src/**/*.ts,src/**/*.py,src/**/*.sh,src/**/*.js'
ixwp:
  layer: domain
  module: iHFM
  weight: 980
  since: 2.0.0
  breaking: false
  requires: [core]
---

<!-- ix.WP V2.0.0 — iHFM headers/footers (domain, loaded on source files) -->

# ix.WP — Cabeçalhão e Rodapé Ir.On (iHFM)

## Ao CRIAR arquivo-fonte:
1. Adicionar cabeçalhão Ir.On no topo
2. Adicionar rodapé Ir.On no final
3. Preencher: título, versão, agent, sessão, data, caminho, detalhes

## Ao MODIFICAR arquivo-fonte:
1. Atualizar `Ultima modificacao:` com data/hora atual
2. Atualizar `Detalhes:` descrevendo a alteração
3. Se não existir header → adicionar

## Modelos

| Modelo | Largura | Quando usar |
|--------|---------|-------------|
| Completo | 81 cols | Sessão + task + detalhes longos |
| Compacto | 69 cols | Metadados médios |
| Ultra-Compacto | 44 cols | Configs simples |

## Adaptação por Linguagem
- **HTML/Markdown:** `<!-- ... -->`
- **JS/TS/CSS:** `// ...` ou `/* ... */`
- **Python/Shell/YAML:** `# ...`

## CRÍTICO
- NUNCA alterar a marca Ir.On (lado esquerdo do header)
- Apenas a coluna direita (metadados) pode ser editada

> Para templates completos e exemplos: `#ix-wp-ihfm`
