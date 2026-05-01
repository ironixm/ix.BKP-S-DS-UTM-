<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ MopGled – Pacote do APP ix.BZP-DealScore-UTM-Sync – V1.0.0 │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-03 - 15:41                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ modulos/mopgled/README.md                                  │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# MopGled – Pacote do APP ix.BZP-DealScore-UTM-Sync

- **APP ID:** 11
- **Tema/Modo:** mopgled-T.1 (single)
- **Domínios autorizados:** replit.dev, replit.app
- **API MopGled:** http://ix-renomeie.onrender.com/mopgled
- **Gerado em:** 2026-02-03T15:23:33.305871
- **CSS:** http://ix-renomeie.onrender.com/mopgled/apps/11/css
- **JS:** http://ix-renomeie.onrender.com/mopgled/apps/11/js
- **ZIP oficial:** http://ix-renomeie.onrender.com/mopgled/apps/11/module

MopGled é o serviço de temas/UI do MadMode. Cada APP cadastrado gera bundles CSS/JS por domínio autorizado e com hash/versionamento para cache seguro. Este módulo empacota os includes e um instalador para plug-and-play em qualquer projeto (Flask, Django, FastAPI, front-end estático, etc).

## O que vem no pacote
- `assets/` – includes prontos (`mopgled_head.html`, `mopgled_scripts.html`) apontando para a API `api.madmode.com.br/mopgled`.
- `manifests/mopgled.json` – metadados do app (ids, tema, `api_base`, defaults de pastas).
- `instalar.py` – instalador/sincronizador: verifica atualização no `http://ix-renomeie.onrender.com/mopgled/apps/11/module`, injeta os includes nos templates e gera backups (TTL 24h) + logs.
- `logs/` e `backups/` – criados em runtime para histórico de execução/restauração.

## Instalação rápida (qualquer projeto)
1. Copie `modulos/mopgled/` para a raiz do projeto.
2. Se o download do módulo exigir token, exporte antes de rodar:
   ```bash
   export ALIXIA_SYNC_TOKEN=seu_token   # ou MOPGLED_SYNC_TOKEN
   ```
3. Execute:
   ```bash
   python3 modulos/mopgled/instalar.py
   ```
   - Por padrão, usa `templates/` como raiz dos HTML (ajuste em `manifests/mopgled.json` se seu projeto usar outro caminho).
   - Inclui automaticamente os snippets de `<head>` e `<body>` e registra um relatório em `logs/last-run.log`.
4. Para front-ends sem Jinja (ex.: SPA/React/Vue), importe manualmente os includes de `assets/` no seu HTML base:
   ```html
   <!-- Head -->
   <link rel="stylesheet" href="http://ix-renomeie.onrender.com/mopgled/apps/11/css">
   <!-- Body -->
   <script type="module" src="http://ix-renomeie.onrender.com/mopgled/apps/11/js"></script>
   ```

## Atualização e sincronização
- O instalador consulta `http://ix-renomeie.onrender.com/mopgled/apps/11/module` (já com host `api.madmode.com.br`) e aplica a versão mais nova do pacote se existir.
- Rode novamente sempre que atualizar tema/domínio no MadMode ou após receber novo ZIP. Backups ficam em `backups/` por 24h.
- Para automação, agende `python3 modulos/mopgled/instalar.py` (cron/systemd) e defina `ALIXIA_SYNC_TOKEN`/`MOPGLED_SYNC_TOKEN` para autorizar o fetch do ZIP.
- Precisa restaurar?
  ```bash
  python3 modulos/mopgled/instalar.py --restore YYYYMMDD_HHMMSS
  ```

## AutoSync multiplataforma (ETag/Last-Modified)
- **Shell genérico:** `modulos/mopgled/autosync.sh` lê o manifest, baixa CSS/JS para `static/` com ETag e salva meta em `logs/autosync.meta.json`. Requer `curl` + `python3`. Variáveis úteis:
  - `TARGET_STATIC_DIR` para alterar o destino (padrão: `../../static`).
  - `MOPGLED_SYNC_TOKEN`/`ALIXIA_SYNC_TOKEN` se o módulo exigir Bearer.
  - `MOPGLED_MANIFEST`/`MOPGLED_META` para apontar paths custom.
  Exemplo: `cd modulos/mopgled && ./autosync.sh`.
- **Node 18+:** `modulos/mopgled/autosync_node.js` faz o mesmo usando `fetch` nativo. Rode `node modulos/mopgled/autosync_node.js` (honra as mesmas variáveis de ambiente acima).
- Use cron/systemd/GitHub Actions para agendar; ambos scripts só escrevem quando há mudança (HTTP 304 preserva arquivos).

## Referência de uso (ix.Inv)
- O app `ix.Inv` mantém cache local dos bundles e revalida via HEAD/ETag (ver `ix.Inv/app/mopgled_sync.py`).
- A mesma abordagem funciona aqui: copie a lógica de ETag em qualquer linguagem ou use os scripts de AutoSync acima para manter `static/mopgled.{css,js}` atualizados.

## Host correto (evitar localhost)
- No servidor MadMode, defina `MOPGLED_EXTERNAL_BASE=https://api.madmode.com.br` (ou `EXTERNAL_API_BASE`), opcionalmente já com `/mopgled`. Isso garante que o ZIP gerado não traga `localhost` em nenhum link.

Boa instalação e bom deploy do MopGled! 🚀

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
