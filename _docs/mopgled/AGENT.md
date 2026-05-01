<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ AGENTE – MopGled Client (ZIP) – V1.0.0         │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _docs/mopgled/AGENT.md                         │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# AGENTE – MopGled Client (ZIP)

## Objetivo
Instalar o MopGled Client em qualquer aplicação, sincronizando CSS/JS via CDN do MadMode, com backup automático e logs claros.

## Checklist rápido
- Confirme `app.id`, `theme_id` e `domains` em `modulos/mopgled-client/manifests/mopgled.json`.
- Valide se `api_base` aponta para `https://api.madmode.com.br/mopgled`.
- Se o download do módulo exigir Bearer, garanta `MOPGLED_SYNC_TOKEN` no ambiente (ou use `--token`).
- O token pode vir preenchido no manifest (campo `auth.sync_token`) quando o ZIP é gerado.

## Execução recomendada
1. Descompacte o ZIP em uma pasta temporária.
2. Rode o instalador com o wrapper:

```bash
python3 instalador/install-py.py --project /caminho/do/projeto
```

3. Verifique o console: deve aparecer `MopGled - OK - <codigo>`.

## Bootstrap (projeto novo)
- Use `--bootstrap` para criar uma estrutura completa de projeto:
  ```bash
  python3 instalador/install-py.py --bootstrap --project /caminho/do/projeto
  ```
- Se o instalador estiver em `_docs/mopgled/`:
  ```bash
  python3 _docs/mopgled/instalador/install-py.py --bootstrap --project .
  ```
- O template cria `_docs`, `.github`, `core`, `models`, `migrations`, `templates`, `static` e copia o MopGled Client.
- Use `--bootstrap-only` se quiser apenas a estrutura, sem injeção.

## Detecção de templates
- O instalador tenta localizar automaticamente diretórios e templates base.
- Se não encontrar, ele oferece opções para:
  - criar um `base.html`,
  - informar um diretório manualmente,
  - pular injeção automática,
  - cancelar.

## SPA / HTML sem Jinja
- Use `--inject-mode raw` para inserir `<link>` e `<script>` diretamente.
- Ou pule a injeção automática e copie manualmente os includes do `assets/`.

## Atualização e restauração
- Reexecute o instalador para aplicar a versão mais recente do ZIP.
- Restaurar backup: `python3 modulos/mopgled-client/instalar.py --restore <timestamp>`.

## Verificação e suporte
- Para decodificar o código de status:

```bash
python3 modulos/mopgled-client/instalar.py --verify "MopGled - OK - <codigo>"
```

- Ao final da instalação, o instalador oferece um checklist rápido e opções de limpeza (remover logs/backups ou manter restore).

## Observação importante
Este pacote instala **mopgled-client** (cliente do serviço). O MopGled completo permanece no MadMode.

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
