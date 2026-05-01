<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – Bootstrap de Projeto (MopGled) – V1.0.0           │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/_docs/entrada/mopgled/AG... │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# AGENTE – Bootstrap de Projeto (MopGled)

## Objetivo
Guiar a criação de um novo projeto seguindo o padrão Ir.On/MadMode. Este arquivo deve ser lido antes de iniciar qualquer tarefa.

## Comando base (bootstrap)
```bash
python3 _docs/mopgled/instalador/install-py.py --bootstrap --project .
```

## Ordem obrigatória
1. Leia `_docs/_cHead.md` e aplique o cabeçalho em **todo** arquivo criado/alterado.
2. Salve o prompt inicial em `_docs/Prompts/000_inicial.md`.
3. Coloque imagens e referências em `_docs/entrada/controle/`.
4. Atualize `_docs/JOBS.md` com o que será feito.
5. Leia `_docs/playbooks/#9 Playbook Projecter-V-Geral.md`.
6. Se estiver usando Codex ou Copilot, leia também:
   - `_docs/playbooks/#9.1 Playbook Projecter-V-CODEX.md`
   - `_docs/playbooks/#9.2 Playbook Projecter-V-COPILLOT.md`

## Regras de projeto
- Sempre manter a estrutura base (core, models, migrations, modulos, static, templates, _docs).
- `modulos/mopgled-client` é obrigatório e já vem pronto.
- `templates/base.html` e `templates/login.html` devem existir desde o início.
- Atualize `requirements.auto.in` e gere `requirements.txt` usando `_Gera_requirements_txt.command`.

## Entregas mínimas
- Estrutura criada e organizada.
- Documentação inicial preenchida.
- JOBS.md atualizado.
- Base do app rodando (mesmo que com placeholders).

## Padrão de commits
- Seguir `.github/COMMIT_CONVENTION.md`.
- Descrever mudanças e atualizar JOBS.
