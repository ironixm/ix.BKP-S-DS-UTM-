<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ MopGled Client – pacote do APP ix.BZP-DealScore-UTM-Syn... │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/README.md                                    │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# MopGled Client – pacote do APP ix.BZP-DealScore-UTM-Sync

Este pacote instala o **MopGled Client** (includes de CSS/JS via CDN). Ele não contém o MopGled completo, apenas o cliente que consome o serviço oficial do MadMode.

**Dados do app**
- APP ID: 11
- Tema/Modo: mopgled-T.1 (single)
- Domínios autorizados: replit.dev, replit.app, replit.com, localhost
- API MopGled: http://api.madmode.com.br/mopgled
- Gerado em: 2026-02-11T15:13:18.601703
- CSS: http://api.madmode.com.br/mopgled/apps/11/css
- JS: http://api.madmode.com.br/mopgled/apps/11/js
- ZIP oficial: http://api.madmode.com.br/mopgled/apps/11/module
- Token de sync (se presente): 141ec870c90d0fb985da18b23727440fd6a13ef7

**Instalação rápida**
1. Descompacte o ZIP em uma pasta temporária.
2. Rode o instalador conforme seu stack:

```bash
# Python
python3 instalador/install-py.py --project /caminho/do/projeto

# Node
node instalador/install-node.js --project /caminho/do/projeto

# Shell
./instalador/install.sh --project /caminho/do/projeto
```

3. Valide o console: deve aparecer `MopGled - OK - <codigo>`.

**Tokens / Bearer**
- Se o token não estiver preenchido acima, defina `MOPGLED_SYNC_TOKEN` no ambiente ou passe `--token`.
- Para salvar no `.env` do projeto: use `--save-token`.
- Para HTML sem Jinja, rode com `--inject-mode raw`.

**Bootstrap de projeto novo**
- Para criar um projeto completo, rode:
  ```bash
  python3 instalador/install-py.py --bootstrap --project /caminho/do/projeto
  ```
- Se você copiou o instalador para `_docs/mopgled/`:
  ```bash
  python3 _docs/mopgled/instalador/install-py.py --bootstrap --project .
  ```
- O bootstrap cria a estrutura base, docs, playbooks, templates, `.github/` e `modulos/mopgled-client`.
- Use `--bootstrap-only` para criar apenas a estrutura (sem injeção nos templates).

**Estrutura do pacote**
- `instalador/` – wrappers do instalador (Python, Node, Shell).
- `modulos/mopgled-client/` – módulo cliente, instalador principal e scripts de sync.
- `project_template/` – template de projeto novo (usado pelo `--bootstrap`).

Dúvidas? Consulte o `AGENT.md` deste pacote.

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
