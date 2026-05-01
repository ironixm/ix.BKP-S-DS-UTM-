<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – Uso do ZIP MopGled – V1.0.0           │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ modulos/mopgled/AGENT.md                       │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# AGENTE – Uso do ZIP MopGled

## Objetivo
Empacotar e instalar o MopGled (CSS/JS temáticos) em qualquer projeto filho do MadMode ou app externo, usando o ZIP gerado na aba **/Tema**.

## Checklist rápido
- Abra `modulos/mopgled/manifests/mopgled.json` e valide:
  - `app.id/theme_id/mode` corretos e `domínios` condizentes com o alvo.
  - `service.api_base` começa com `https://api.madmode.com.br/mopgled` (evitar `app.madmode.com.br`).
- Exporte token antes de rodar o instalador se o download do módulo for protegido:
  - `ALIXIA_SYNC_TOKEN` ou `MOPGLED_SYNC_TOKEN`.
- Confirme o diretório de templates esperado (`defaults.templates_dir`, padrão `templates`).

## Execução padrão (Flask/Django/Jinja)
1) Copie `modulos/mopgled/` para a raiz do projeto alvo.  
2) Rode `python3 modulos/mopgled/instalar.py`.  
   - Ele baixa versão mais nova do ZIP via `http://ix-renomeie.onrender.com/mopgled/apps/11/module`, aplica includes em `<head>`/`<body>`, gera `logs/last-run.log` e backup com TTL 24h.  
3) Valide carregamento:
   - Network deve apontar para `api.madmode.com.br/mopgled/apps/<id>/{css,js}`.
   - `window.MopGled` presente no console.

## Execução em SPA/estático
- Não use injeção automática; inclua manualmente os snippets de `assets/` no HTML base (CSS no `<head>`, JS com `type="module"` antes de fechar `<body>`).
- Se quiser cache local/offline, faça fetch dos bundles do manifest e salve em `static/`, seguindo o padrão de revalidação usado em `ix.Inv/app/mopgled_sync.py`.

## Atualização e suporte
- Re-rodar `instalar.py` sempre que mudar tema/domínios no MadMode; o script verifica e aplica o ZIP mais recente (API host).
- Para automação, agende execução (cron/systemd) com `ALIXIA_SYNC_TOKEN`/`MOPGLED_SYNC_TOKEN` no ambiente.
- Restaurar backup: `python3 modulos/mopgled/instalar.py --restore <timestamp>`.

## Referências
- Serviço MopGled (API/tema): `api.madmode.com.br/mopgled`.
- Pacote gerado originalmente em `modulos/mopgled/module_template` (fonte da verdade dos includes/instalador).
- Exemplo de consumidor: `ix.Inv` usa sync condicional com HEAD/ETag (`ix.Inv/app/mopgled_sync.py`) para manter bundles atuais. 

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
