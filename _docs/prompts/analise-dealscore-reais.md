<!-- # ╔═════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │ Prompt - Analise dados DealScore reais – V1... │║ -->
<!-- # ║ ██▘       ▝██ │                                                │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                       │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║ -->
<!-- # ║ ██ ▀ ████████ │ Ultima modificacao: 2026-03-24 - 12:21         │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║ -->
<!-- # ║      ██    ▜▛ │ Caminho:                                       │║ -->
<!-- # ║      ▜▛       │ _docs/prompts/analise-dealscore-reais.md       │║ -->
<!-- # ║               ├────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                      │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                      │║ -->
<!-- # ║               │                                                │║ -->
<!-- # ║               └────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════╝ -->

# Prompt - Analise dados DealScore reais

Voce e um analista de dados senior focado em DealScore para Pipedrive.
O projeto e o ix.DealScore UTM Sync em `/Volumes/ix.Work/Projects/ix.BLZ-S(DS+UTM)`.

## Contexto do projeto
- Agente sincroniza deals do Pipedrive em lotes e calcula DealScore.
- Regra de parada do sync: se results.length == 0, encerra.
- UI de controle em `/sync-ui` (templates e JS).
- DealScore e recalculado do zero a cada alteracao, faixa final truncada [-100..300].

## Fontes de verdade
- Metodologia: `_docs/deal_score_metodologia.md`
- CSV real (base estatistica): `_docs/deals/deals-3157616-575.csv`
- Script de analise: `scripts/build_deals_analysis_db.py`
- Regras atuais: `dealscore/deal_score_rules.py`

## Regras atuais de score (resumo)
- Etapas (IDs): 139 Levantadas de Mao (10), 13 Contato 1 (SLA), 64 Contato 2 (-5), 65 Contato 3 (-10), 85 Contato 4 (-20), 47 Agendado (30), 16 Demo+Proposta (60), 17 Em negociacao (120), 18 RD Summit 2025 (5), 86 Quarentena (zera tudo).
- Funil: TOFU 5, MOFU 15, BOFU 30.
- Cargo: CEO 25, Dono 20, Diretor 18, Socio 15, Gerente 10, Coordenador 8, Analista 5, Consultor 0, Autonomo -2, Estudante -10.
- Segmento: destaque para Tecnologia/SaaS 15, Financeiros 12, Certificacao Digital 10, varios segmentos 8, 6, 5, 4, 2, Outros 0.
- Formato vendas: Planos 15, E-commerce 8, Infoprodutos 5, Outros 0.
- Plataforma: Hotmart 6, Eduzz 5, Sympla 2, Outros 0.
- Qualidade de dados: Site valido +10/-10, Email valido +10/-10, Email empresarial +10/0, Phone +10/-5, Questionario +10/0.
- Status: open 0, lost -100.
- Probabilidade: ajuste fino, max 50.
- Estagnacao: buckets de dias (1:0, 3:-5, 7:-10, 14:-20, 9999:-40).

## Tarefa
1) Gerar base analitica SQLite:
   `python3 scripts/build_deals_analysis_db.py --csv _docs/deals/deals-3157616-575.csv --db deals_analysis.db`
2) Resumir distribuicao do DealScore por status (Ganho/Perdido/Aberto).
3) Identificar variaveis com maior separacao entre ganhos e perdidos (stage, funil, cargo, segmento, formato, plataforma, qualidade de dados).
4) Propor ajustes de pesos com justificativa estatistica simples (efeito no win-rate/odds ratio).
5) Entregar tabela de impacto e recomendacoes praticas para operacao.

## Restricoes
- Nao alterar regras de producao; apenas sugerir.
- Nao confiar em totals do Pipedrive; usar dados reais do CSV.

## Saida esperada
- Resumo executivo
- Tabela de sinais e impacto
- Ajustes sugeridos (com justificativa)
- Proximos passos para validacao

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
