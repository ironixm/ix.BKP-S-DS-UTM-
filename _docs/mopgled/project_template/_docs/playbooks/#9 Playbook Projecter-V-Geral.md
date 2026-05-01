<!-- # ╔═════════════════════════════════════════════════════════════════════════════╗ -->
<!-- # ║    ▄▄███▄▄    ┌────────────────────────────────────────────────────────────┐║ -->
<!-- # ║  ▄█▛▘‾ ‾▝▜█▄  │  Playbook #9 — Projecter (V-GERAL) – V1.0.0                │║ -->
<!-- # ║ ██▘       ▝██ │                                                            │║ -->
<!-- # ║ ██▖       ▗██ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║ ███▄_   _▄███ │ By Ir.On                                                   │║ -->
<!-- # ║ █████████████ │ Agent: Copilot | Sessao: branch:main                       │║ -->
<!-- # ║ ██ ▀ ████████ │ commit:f563b5b                                             │║ -->
<!-- # ║ ██ ● ██▀██▀██ │ Ultima modificacao: 2026-02-11 - 12:13                     │║ -->
<!-- # ║ ▜▛   ██ ▜▛ ██ │ ironix.com.br                                              │║ -->
<!-- # ║      ██    ▜▛ ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║      ▜▛       │ Caminho:                                                   │║ -->
<!-- # ║               │ _docs/mopgled/project_template/_docs/playbooks/#9 Playb... │║ -->
<!-- # ║               ├────────────────────────────────────────────────────────────┤║ -->
<!-- # ║               │ Detalhes:                                                  │║ -->
<!-- # ║               │ * V1.0.0 - [sem detalhes]                                  │║ -->
<!-- # ║               │                                                            │║ -->
<!-- # ║               └────────────────────────────────────────────────────────────┘║ -->
<!-- # ╚═════════════════════════════════════════════════════════════════════════════╝ -->

# 🧩 Playbook #9 — Projecter (V-GERAL)

**Título:** Como Criar Projetos de Verdade em Markdown (Estilo Alíxia Σ)  
**Versão:** v1.2  
**Público:** Humanos · Agentes (Copilot, CODEX, LLMs) · Custom GPT Alíxia Σ  
**Status:** Documento Canônico

---

## 🧠 Manifesto — “Projeto é memória executável”

Projeto não é texto bonito.  
Projeto é **memória organizada para execução contínua**.

Um projeto só é válido se:
- outro agente consegue continuar
- outra conversa consegue retomar
- outra semana não perde contexto

> “Se precisa explicar fora do MD, o projeto falhou.” — Σ

---

## 🎯 Objetivo do Projecter

Ensinar **como pensar, escrever e manter projetos** que:

- sobrevivem à troca de agente
- sobrevivem ao limite de tokens
- funcionam como fonte de verdade
- permitem pausa e retomada sem perda cognitiva

---

## 🧩 O que é um Projeto (definição Alíxia Σ)

Um **Projeto de Verdade** sempre contém:

1. Intenção clara (Manifesto)
2. Delimitação explícita (Escopo)
3. Estrutura compreensível (Arquitetura)
4. Execução reproduzível (Fluxos)
5. Memória viva (JOBS / AGENT / PROMPTS)
6. Continuidade garantida (Prompt de Handoff)

Sem isso → é apenas texto.

---

## ⚙️ Estrutura Padrão Projecter

Todo projeto segue **obrigatoriamente**:

1. Manifesto  
2. Capítulos Técnicos (1–11)  
3. Prompt de Continuidade / Executor  

Cada capítulo **termina com Próximos Passos**.

---

## 📘 Capítulos Técnicos — Estrutura Oficial

### 1. Visão Geral
Resumo executivo do projeto.

- **Serve para:** entender rapidamente do que se trata  
- **Pergunta-chave:** “O que é isso?”

---

### 2. Objetivos
Define o que é sucesso.

- **Serve para:** evitar projetos infinitos  
- **Pergunta:** “Quando termina?”

---

### 3. Público / Agentes Envolvidos
Quem executa, revisa e decide.

- **Serve para:** evitar decisões erradas  
- **Pergunta:** “Para quem isso existe?”

---

### 4. Escopo
O que entra **e o que não entra**.

- **Serve para:** evitar retrabalho  
- **Pergunta:** “Até onde vai?”

---

### 5. Estratégia
A lógica por trás das decisões.

- **Serve para:** manter coerência  
- **Pergunta:** “Por que este caminho?”

---

### 6. Arquitetura
Estrutura técnica ou conceitual.

- **Serve para:** organizar o sistema  
- **Pergunta:** “Como isso se sustenta?”

---

### 7. Fluxos e Execução
Passo a passo real.

- **Serve para:** executar sem você  
- **Pergunta:** “O que faço agora?”

---

### 8. Indicadores / Critérios de Aceite
Como saber que está pronto.

- **Serve para:** finalizar  
- **Pergunta:** “Está correto?”

---

### 9. Riscos e Dependências
O que pode quebrar ou atrasar.

---

### 10. Roadmap
Fases futuras e evolução.

---

### 11. Governança
Como manter, revisar e versionar.

---

## 🧠 Comportamento Obrigatório — JOBS.md

Todo projeto **mantém um arquivo vivo** em:

`/_docs/JOBS.md`

### Função
- registrar tarefas
- separar contextos
- manter rastreabilidade por conversa

### Exemplo real de JOBS.md

```md
# **Alíxia-G — JOBS**

## **🔴 Abertos**
- 06/02/26-11:45 — Garantir reconexão automática estável do controle BT principal após reboot/power-cycle — **OPEN** — ass.: ix.alxG-01-resumo-estado-atual-06-02-2026
- 06/02/26-11:50 — Suporte a mapeamento híbrido por função — **OPEN** — ass.: ix.alxG-01-resumo-estado-atual-06-02-2026

---
## **▶️ Em execução**
- 06/02/26-12:00 — Estabilização de input no PI0 — **IN PROGRESS** — ass.: ix.alxG-01-resumo-estado-atual-06-02-2026

---
## *✅ Concluídos*
- 06/02/26-10:30 — Audio engine retry MIDI — **DONE** — ass.: ix.alxG-01-resumo-estado-atual-06-02-2026

---
## *🖥️ Conversas (log)*
- 06/02/26-11:45 — ix.alxG-01-prompt-AutomatizarRenameConversa — **ACTIVE** — ass.: ix.alxG-01-prompt-AutomatizarRenameConversa






---
*Convenção (assinatura)*
- Preferir assinatura por **ID da conversa** (rastreabilidade): ass.: <conversation_id>
- Ex.: ass.: ix.alxG-01-prompt-CorrigindoFlickerHDMI-01-060226-1115
- Onde:
	- ix - STAMP geral da agência
	- alxG-01 - ID do projeto
	- prompt-CorrigindoFlickerHDMI - Objetivo/FIX/Interesse principal/motivo da conversa
	- 01 - ID da conversa, quando um contexto enche a conversa, e precisamos continuar a mesma conversa em um novo chat
	- 060226-1115 - Data e hora da conversa... tipo DDMMAA-hhmm

```

---

## **🧠 Comportamento Obrigatório — AGENT.md**

Toda pasta relevante do projeto **possui um AGENT.md** explicando:

* objetivo da pasta
* responsabilidades
* o que **não** deve existir ali
* conexões com o resto do projeto

Isso permite **entrada de novos agentes sem onboarding humano**.

---

## **🧠 Comportamento Obrigatório — PROMPTS (handoff)**

Local:

/_docs/prompts/

### **Template oficial de Prompt**

```md
🎯 Objetivo: <1 frase>
**🎯 Objetivo:** <1 frase>  
**💻 Device (opcional):** <PI0|PI5|mac|...>

---

## 🔍 Contexto Atual (resumo)
- 

## ✅ O que já foi feito
- 

## 📂 Estado do código / arquivos relevantes
- JOBS.md
- 

## 💡 Decisões / hipóteses
- 

## ▶️ Próximos passos (copy/paste)
# 1)
# 2)

## Assinatura para JOBS.md
- Use: ass.: <conversation_id>

```

### Exemplo real de Prompt de Handoff

```md
# 💬 PROMPT DE HANDOFF — Alíxia-G no PI0 (continuação amanhã)

📅 Data: 07/02/26  
🎯 Objetivo: Continuar estabilização HDMI + BT  
💻 Device: PI0

## 🔍 Contexto rápido
Projeto `ix.Alíxia-G` rodando em Raspberry Pi Zero (`pi0-home`).
Rodada de hotfix aplicada.

## 📂 Arquivos principais
- `alixia_g/app.py`
- `alixia_g/emulator.py`
- `alixia_g/bluetooth.py`
- `JOBS.md`

## 🐛 Problemas encontrados
1. Flicker HDMI ao abrir RetroArch
2. Reconexão BT instável

## ✅ Problemas resolvidos
- Ajuste de driver SDL2
- Reconnect BT periódico

## ▶️ Próximos passos
1. Teste presencial na TV
2. Validar reconexão BT sem pareamento

```

---

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
