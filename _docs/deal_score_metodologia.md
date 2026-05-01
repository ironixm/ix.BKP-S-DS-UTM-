<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │  DealScore BuzzLead — Metodologia, Pontuações e Justifi... │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:56                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/deal_score_metodologia.md                            │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# 📊 DealScore BuzzLead — Metodologia, Pontuações e Justificativa (v2026-02-04)

Este documento define a metodologia oficial do `ix.DealScore` (BuzzLead), com:

* Regras e pontuações **exatas**
* Derivações (campos “virtuais”)
* Evidência estatística baseada em export real
* Faixas (emoji) para priorização operacional

**Regra de ouro:** score serve para **mandar agir**, não para confortar vendedor.

---

## 🎯 Objetivo do `ix.DealScore`

Priorizar oportunidades com maior probabilidade de conversão **e** maior “temperatura operacional”, considerando:

* Estágio atual (principal separador)
* Movimento real (atividade e/ou avanço de etapa)
* Qualidade mínima do dado (contato e site)
* Sinais fortes de processo (questionário e atividades)
* Funil (TOFU/MOFU/BOFU) derivado da campanha

**Importante:** o score **não é acumulativo**. Ele é **recalculado do zero** a cada alteração.

Faixa final do score é truncada em: `[-100 .. 300]`.

---

## 📦 Base Estatística (export usado nas decisões)

Arquivo base (pipeline real):

* `_docs/deals/deals-3157616-575.csv`

Foto da base (nesta versão do documento):

* Total: 1096 deals
* Status: 822 `Perdido`, 225 `Aberto`, 49 `Ganho`
* Fechados (Ganho/Perdido): 871
* Baseline (fechados): `49/871 = 5,63%` de ganho

Limitações conhecidas do export:

* Não existe trilha de etapas percorridas (só etapa atual + “última alteração de etapa”).
* “Data da última atividade” tem muitos vazios (em `Perdido`, 609/822 sem data).
* “Valor” e “Valor de produtos” tendem a ser preenchidos tardiamente (viés de processo).

---

## 📌 O Que Os Dados Mostraram (indicadores mais relevantes)

### Atualização 2026-02-11 (base CSV real)

**Distribuição do score (score_calculado_atual):**

| Status | n | Media | Mediana | Min | Max |
|---|---:|---:|---:|---:|---:|
| Perdido | 822 | -73,29 | -100 | -100 | 118 |
| Aberto | 225 | 51,15 | 48 | -20 | 176 |
| Ganho | 49 | 144,27 | 150 | 10 | 245 |

**Faixas de score x win-rate (fechados):**

| Score | n | Win-rate |
|---|---:|---:|
| <= 0 | 776 | 0,0% |
| 1-50 | 33 | 12,1% |
| 51-100 | 20 | 25,0% |
| 101-150 | 21 | 90,5% |
| 151-200 | 15 | 100,0% |
| 201-300 | 6 | 100,0% |

**Sinais com maior separação (fechados):**

* **Questionario preenchido**: win-rate 29,2% (42/144) vs 1,0% (7/727).  
  Odds ratio ~ 39,8 (sinal fortissimo).
* **Site preenchido**: win-rate 9,4% (44/469) vs 1,2% (5/402).  
  Odds ratio ~ 7,6 (sinal forte).
* **Etapa atual**: Em negociacao tem win-rate ~ 76,4% (42/55).  
  Etapas de contato tem win-rate ~ 0% no export.

**Mudancas aplicadas nas regras (v2026-02-11):**

* Questionario: **+20** (antes +10).
* Site valido: **+15 / -15** (antes +10 / -10).
* Formato de vendas: incluir **Consultivo = +12**.

### 1) Stage atual é o maior separador (fechados)

Win-rate em **fechados** por etapa atual:

| Etapa (atual) | n | Ganhos | Win-rate |
|---|---:|---:|---:|
| Em negociação | 55 | 42 | 76,36% |
| Agendado | 15 | 3 | 20,00% |
| Dem. + Proposta | 63 | 4 | 6,35% |
| Contato 01 | 74 | 0 | 0,00% |
| Contato 02 | 35 | 0 | 0,00% |
| Contato 03 | 26 | 0 | 0,00% |
| Contato 04 | 577 | 0 | 0,00% |

Leitura prática:

* Stage por si só separa muito bem.
* “Contato 04” é quarentena informal (grande cemitério de pipeline).

### 2) Questionário é um sinal forte (fechados)

Win-rate em fechados por questionário:

| Questionário | n | Ganhos | Win-rate |
|---|---:|---:|---:|
| Sim | 144 | 42 | 29,17% |
| Não | 8 | 3 | 37,50% |
| NA (vazio) | 719 | 4 | 0,56% |

Leitura prática:

* Não é só “perfil”: é “processo real”. Questionário preenchido acompanha deals que de fato andam.

### 3) Movimento real precisa vencer “update administrativo” (abertos)

No export, existe grande volume de:

* Deals abertos com `Atualizado em` recente, mas sem movimento real há muito tempo.

Na foto analisada:

* 36/225 abertos (16%) foram atualizados nos últimos 7 dias, mas o último movimento (atividade ou troca de etapa) tinha 30+ dias.

Decisão: estagnação deve usar **movimento real**, não somente `Atualizado em`.

### 4) Valor não pode mandar no score (viés)

Nesta base, “valor preenchido” aparece associado a ganho de forma artificial (indicando preenchimento tardio).

Decisão: **0 pontos de valor no DealScore** (por enquanto).

---

## 🧠 Conceitos e Derivações Oficiais

### 1) Funil Virtual (TOFU/MOFU/BOFU) — derivado de `Campanha`

Este é o “campo virtual” oficial do funil. Precedência:

1. Se contém `KTL` e contém `(K)` ou `(L)` ou `(T)` → `TOFU`
2. Se começa com `ix.T` → `TOFU`
3. Se começa com `ix.M` → `MOFU`
4. Se começa com `ix.B` → `BOFU`
5. Fallback:
* Se contém `-F1` ou `.F1` → `TOFU`
* Se contém `-F2` ou `.F2` → `MOFU`
* Se contém `-F3` ou `.F3` → `BOFU`

Caso nenhum padrão seja detectado: `NULL` (0 pontos).

### 2) Movimento Real (anti-ilusão de pipeline)

Definição:

* `last_movement_time = max(Data da última atividade, Última alteração de etapa)`
* Fallback: se ambos vazios, usar `Atualizado em` (defensivo)
* `dias_sem_movimento = hoje - last_movement_time`

### 3) Probabilidade do Pipedrive (operacional)

Vamos preencher o campo `probability` no Pipedrive por etapa (SLA operacional), mas **probabilidade não deve dominar o DealScore**.

Tabela operacional (Pipedrive):

| Etapa | Probabilidade (%) |
|---|---:|
| Levantada de mão | 5 |
| Contato 01 | 20 |
| Contato 02 | 15 |
| Contato 03 | 10 |
| Contato 04 | 5 |
| Agendado | 35 |
| Dem. + Proposta | 60 |
| Em negociação | 80 |
| Quarentena | 5 |

Decisão de pontuação no DealScore:

* `probability` = 0 pontos (evita duplicar o peso do stage).

---

## 🧮 Pontuação Oficial (números exatos)

### 0) Overrides (regras que vencem tudo)

* Se `Status == Perdido` → score final = `-100`
* Se `Etapa == Quarentena` → score final = `+5`

Justificativa:

* “Perdido” não é prioridade operacional.
* “Quarentena” mantém uma luz no fim do túnel, mas não pode competir com deals ativos.

### 1) Stage (Etapa) — principal driver

| Etapa | Pontos |
|---|---:|
| Levantadas de Mão | +5 |
| Contato 01 | SLA (0 a +20) |
| Contato 02 | -5 |
| Contato 03 | -10 |
| Contato 04 | -20 |
| Leads RD Summit 2025 | +5 |
| Agendado | +35 |
| Dem. + Proposta | +60 |
| Em negociação | +90 |

SLA de Contato 01 (proxy, criado → 1º movimento):

| SLA | Pontos |
|---|---:|
| <= 4h | +20 |
| <= 8h | +10 |
| <= 24h | +5 |
| > 24h | +0 |

### 2) Funil Virtual (derivado da campanha)

| Funil | Pontos |
|---|---:|
| TOFU | +5 |
| MOFU | +10 |
| BOFU | +20 |
| NULL | 0 |

### 3) Qualidade do dado (leve, sem mascarar inércia)

| Critério | Pontos |
|---|---:|
| Site válido | +10 |
| Site inválido | -10 |
| Email válido | +5 |
| Email inválido | -10 |
| Telefone válido | +5 |
| Telefone inválido | -5 |
| Email empresarial | 0 |

Questionário:

| Valor | Pontos |
|---|---:|
| Sim | +20 |
| Não | -10 |
| NA (vazio) | 0 |

### 4) Atividades (proxy de engajamento real)

Regra baseada em `Negócio - Total de atividades` (fechados mostraram forte associação com ganho):

| Atividades | Pontos |
|---|---:|
| 0 | -10 |
| 1 | 0 |
| 2–3 | +5 |
| 4–5 | +10 |
| 6–10 | +8 |
| 11+ | +4 |

### 5) Movimento (estagnação por movimento real)

Penalidade por `dias_sem_movimento`:

| Dias sem movimento | Pontos |
|---|---:|
| 0–1 | 0 |
| 2–3 | -5 |
| 4–7 | -15 |
| 8–14 | -30 |
| 15–30 | -60 |
| 31–60 | -90 |
| 61+ | -120 |

Caps anti-ilusão (recomendados como regra de negócio):

* Se `dias_sem_movimento >= 30` → score máximo = `100`
* Se `dias_sem_movimento >= 60` → score máximo = `60`

### 6) Perfil (mantido, mas não pode ser obrigatório)

Pontos por Cargo (Pessoa):

| Cargo | Pontos |
|---|---:|
| CEO | +25 |
| Dono/Proprietário(a) | +20 |
| Diretor(a) | +18 |
| Sócio(a) | +15 |
| Gerente de Marketing/Vendas | +10 |
| Coordenador de Marketing/Vendas | +8 |
| Analista de Marketing/Vendas | +5 |
| Consultor(a) | 0 |
| Autônomo | -2 |
| Estudante | -10 |

Pontos por Segmento (Pessoa):

| Segmento | Pontos |
|---|---:|
| Tecnologia/Software/SaaS | +15 |
| Financeiros/Crédito | +12 |
| Certificação Digital | +10 |
| Educação | +8 |
| Incorporação/Imobiliária | +8 |
| Saúde e bem estar | +8 |
| Energia solar | +8 |
| Corretoras e seguradoras | +8 |
| Seguros | +8 |
| Contabilidade | +6 |
| Consultorias | +6 |
| Varejo | +6 |
| Turismo e Hotelaria | +5 |
| Internet e Telefonia | +5 |
| Alimentação | +4 |
| Esporte e lazer | +4 |
| Agência de marketing | +2 |
| Outros | 0 |

Pontos por Formato de vendas (Pessoa):

| Formato | Pontos |
|---|---:|
| Planos/assinaturas/mensalidades | +15 |
| E-commerce | +8 |
| Lançamento de Infoprodutos | +5 |
| Outros | 0 |

Plataforma de vendas (Deal):

| Plataforma | Pontos |
|---|---:|
| Hotmart | +6 |
| Eduzz | +5 |
| Sympla | +2 |
| Outros | 0 |

### 7) Valor (Deal)

* Pontos no DealScore: **0**
* Uso permitido: desempate dentro da mesma faixa e comunicação (ex.: LTV = `12xMRR + Setup`)

---

## 🏷️ Faixas Operacionais (Emoji no nome do Deal)

As faixas são calculadas sobre o score final:

* `-100 a 0` → 🧊 Deal frio/morto (não é prioridade operacional)
* `1 a 100` → 👀 Baixa prioridade (tem sinais, mas não é agora)
* `101 a 200` → ⚡ Alta prioridade (trabalhar com foco)
* `201+` → 🔥 Quase ganho / estratégico

Regras:

* Se `Status == Perdido` → 🧊 (sempre)
* Se `Etapa == Quarentena` → 👀 (score=5)

---

## 🔧 Implementação (Webhook / Sync)

* Recalcula tudo a cada update
* Grava no campo `ix.DealScore`
* Logs com breakdown (auditável)

---

## 🔜 Próximos passos (após aprovação)

1. Ajustar implementação (`dealscore/deal_score.py`) para:
* Funil virtual v2 (campanha → TOFU/MOFU/BOFU)
* Estagnação por movimento real
* Overrides e caps
* Probabilidade com 0 pontos (ou peso mínimo, se aprovado)
2. Automação de emoji no nome do deal (sem loop infinito, via sync controlado)

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
