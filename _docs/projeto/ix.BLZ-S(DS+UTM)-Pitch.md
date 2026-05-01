<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ ix.BLZ-S(DS+UTM) — Pitch – V1.0.0                         │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessão: ix.WP-EXT-V1.5.6|Pitches-Batch2  │║ -->
<!-- # ║ ██ ▀ ████████ │ 190326-1425                                               │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-03-19 - 14:25                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/projeto/ix.BLZ-S(DS+UTM)-Pitch.md                    │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * Pitch manual baseado em evidências (Pipedrive sync UI)  │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# ix.BLZ-S(DS+UTM) - Pitch

ix.BLZ-S(DS+UTM) (ix.DealScore · UTM Sync) é um serviço em Flask com UI (`/sync-ui` e `/dates-ui`) para sincronizar Deals do Pipedrive em lotes controlados, derivar UTMs a partir de campanhas e calcular/gravar um DealScore com trilha de logs.

O problema que ele ataca é clássico de operação comercial: CRM com dados incompletos/inconsistentes vira “decisão no escuro”. Aqui, o pipeline padroniza a captura (UTM) e cria um scoring objetivo para priorização, auditoria e melhoria contínua.

O diferencial é segurança operacional: modo `test` vs `write`, execução incremental (termina quando a API retorna zero itens) e controle manual via interface — ideal para backfills grandes sem travar a operação ou cair em loops infinitos.

Como produto interno, isso vira alavanca imediata: melhora atribuição, qualidade de dados e previsibilidade de receita, liberando o time para otimizar o funil com base em evidência e não em suposição.

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
