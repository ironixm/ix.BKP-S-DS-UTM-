<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Convenção de Commits - ix.renomeie – V4.1.0                │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/.github/COMMIT_CONVENTIO... │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V4.1.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# Convenção de Commits - ix.renomeie

## Formato Obrigatório

Todos os commits e títulos de PR devem seguir o padrão:

```
Vx.y.z - ModuloX|ModuloY - Titulo - TIPO - DDMMYYHHMM
```

### Componentes

- **Vx.y.z**: Versão semântica (ex: V4.0.31, V4.0.32)
- **ModuloX|ModuloY**: Módulos afetados separados por `|` (opcional)
- **Titulo**: Descrição resumida da mudança
- **TIPO**: Tipo da mudança
  - `FEAT`: Nova funcionalidade ou recurso
  - `FIX`: Correção de bug ou problema
  - `DOCS`: Mudanças em documentação
  - `REFACTOR`: Refatoração de código (sem mudança de comportamento)
  - `TEST`: Adição ou modificação de testes
  - `CHORE`: Tarefas de manutenção (atualização de dependências, configurações, scripts de build, etc.)
- **DDMMYYHHMM**: Data e hora no formato dia(2), mês(2), ano(2), hora(2), minuto(2)

### Exemplos

```
V4.0.31 - Merge origin/main - FIX - 2912251239
V4.0.32 - SmartGlue|Dashboard - Adiciona validação de CORS - FEAT - 2912251601
V4.0.33 - core - Atualiza documentação de API - DOCS - 2912251605
V4.0.34 - core - Atualiza dependências do Poetry - CHORE - 2912251610
V4.2.10 - ix_cf_workers - imm.wtf bypass Turnstile - FEAT - 1001261015
```

### O que é CHORE?

`CHORE` (tarefa/afazer) refere-se a mudanças que não afetam diretamente o código de produção ou funcionalidades, mas são necessárias para manter o projeto. Exemplos:

- Atualização de dependências (package.json, requirements.txt, poetry.lock)
- Mudanças em scripts de build ou deploy
- Configurações de CI/CD
- Limpeza de código morto ou comentários
- Reorganização de estrutura de arquivos (sem mudança de lógica)

## Body do Commit (Opcional)

O corpo do commit pode conter detalhes em Markdown:

```markdown
## ModuloX
- Detalhes em Markdown (pontos principais)
---
## ModuloY
- Relacionar integrações/bancos modificados
```

## Validação

O workflow `.github/workflows/commit-format.yml` valida automaticamente:
- Títulos de PR
- Mensagens de commit

Commits que não seguem este padrão falharão na CI/CD.

## Referências

- Template: `.gitmessage`
- Workflow: `.github/workflows/commit-format.yml`

<!--
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
-->
