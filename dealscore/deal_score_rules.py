# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Deal Score Rules – V1.0.0                      │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:55         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ dealscore/deal_score_rules.py                  │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# =====================================================
# CONFIG
# =====================================================

# Campo (Deal) onde gravar o score final
DEAL_SCORE_FIELD_ID = "6ecee6457426bc4cc8f2fcce89b14baf3793ecfe"

# Campo de profundidade do funil (Deal)
PROFUNDIDADE_FUNIL_FIELD_ID = "8ba3c6ef23c1678a96c41b51748a7a8bf6fda577"

# =====================================================
# PIPELINE / STAGES
# =====================================================

STAGE_LEVANTADA_MAO = 139
STAGE_CONTATO_1 = 13
STAGE_CONTATO_2 = 64
STAGE_CONTATO_3 = 65
STAGE_CONTATO_4 = 85
STAGE_RD_SUMMIT_2025 = 18
STAGE_AGENDADO = 47
STAGE_DEMO_PROPOSTA = 16
STAGE_NEGOCIACAO = 17
STAGE_QUARENTENA = 86

# Scores fixos por etapa (exceto Contato 1)
STAGE_SCORES = {
    STAGE_LEVANTADA_MAO: 5,    # doc: +5
    STAGE_CONTATO_2: -5,
    STAGE_CONTATO_3: -10,
    STAGE_CONTATO_4: -20,
    STAGE_AGENDADO: 35,         # doc: +35
    STAGE_DEMO_PROPOSTA: 60,
    STAGE_NEGOCIACAO: 90,       # doc: +90
    STAGE_RD_SUMMIT_2025: 5,
}

# Contato 1 → SLA em horas (proxy via add_time → primeiro movimento)
CONTACT1_SLA_BUCKETS = [
    (4, 20),
    (8, 10),
    (24, 5),
    (9999, 0),  # >24h = 0
]

# Quarentena zera tudo
RESET_STAGES = {STAGE_QUARENTENA}

# =====================================================
# FUNIL
# =====================================================

FUNIL_SCORES = {
    "TOFU": 5,
    "MOFU": 10,   # doc: +10
    "BOFU": 20,   # doc: +20
}

# =====================================================
# CARGO (Person)
# =====================================================

CARGO_SCORES = {
    "CEO": 25,
    "Dono/Proprietário(a)": 20,
    "Diretor(a)": 18,
    "Sócio(a)": 15,
    "Gerente de Marketing/Vendas": 10,
    "Coordenador de Marketing/Vendas": 8,
    "Analista de Marketing/Vendas": 5,
    "Consultor(a)": 0,
    "Autônomo": -2,
    "Estudante": -10,
}

# =====================================================
# SEGMENTO (Person)
# =====================================================

SEGMENTO_SCORES = {
    "Tecnologia/Software/SaaS": 15,
    "Financeiros/Crédito": 12,
    "Certificação Digital": 10,
    "Educação": 8,
    "Incorporação/Imobiliária": 8,
    "Saúde e bem estar": 8,
    "Energia solar": 8,
    "Corretoras e seguradoras": 8,
    "Seguros": 8,
    "Contabilidade": 6,
    "Consultorias": 6,
    "Varejo": 6,
    "Turismo e Hotelaria": 5,
    "Internet e Telefonia": 5,
    "Alimentação": 4,
    "Esporte e lazer": 4,
    "Agência de marketing": 2,
    "Outros": 0,
}

# =====================================================
# FORMATO DE VENDAS (Person)
# =====================================================

FORMATO_VENDAS_SCORES = {
    "Planos/assinaturas/mensalidades": 15,
    "E-commerce": 8,
    "Consultivo": 12,
    "consultivo": 12,
    "Lançamento de Infoprodutos": 5,
    "Outros": 0,
}

# =====================================================
# PLATAFORMA (Deal)
# =====================================================

PLATAFORMA_SCORES = {
    "Hotmart": 6,
    "Eduzz": 5,
    "Sympla": 2,
    "Outros": 0,
}

# =====================================================
# QUALIDADE DOS DADOS
# =====================================================

SITE_VALIDO_SCORES = {"Sim": 10, "Não": -10}       # doc: +10/-10
EMAIL_VALIDO_SCORES = {"Sim": 5, "Não": -10}        # doc: +5/-10
EMAIL_EMPRESARIAL_SCORES = {"Sim": 0, "Não": 0}     # doc: 0 (sem bônus)
PHONE_VALIDO_SCORES = {"Sim": 5, "Não": -5}         # doc: +5/-5
QUESTIONARIO_SCORES = {"Sim": 20, "Não": -10}       # doc: Sim=+20, Não=-10

# =====================================================
# STATUS / PROBABILIDADE
# =====================================================

# Status NÃO adiciona score positivo — lost é override direto em compute_deal_score
STATUS_SCORES = {
    "open": 0,
    "lost": -100,
}

# Probabilidade: 0 pontos (evita duplicar peso do stage)
PROBABILITY_MAX_POINTS = 0

# =====================================================
# ESTAGNAÇÃO
# =====================================================

STAGNATION_BUCKETS_DAYS = [
    (1, 0),
    (3, -5),
    (7, -15),
    (14, -30),
    (30, -60),
    (60, -90),
    (9999, -120),
]

# Caps anti-ilusão: deals parados por muito tempo não podem ter score alto
STAGNATION_CAPS = [
    (60, 60),   # ≥60d → max 60  (mais restritivo primeiro)
    (30, 100),  # ≥30d → max 100
]

# =====================================================
# EMOJI FAIXAS (fonte única de verdade)
# =====================================================
# Mapeamento: score → emoji plantinha
#   🪨  ≤ 0    morto/frio
#   🌱  1–50   semente (baixíssimo)
#   🌿  51–100 crescendo (tem sinais, não é agora)
#   🌳  101–200 alta prioridade (trabalhar com foco)
#   🍀  201+   estratégico / quase ganho

EMOJI_TIERS: list[tuple[int, str]] = [
    (0,   "🪨"),
    (50,  "🌱"),
    (100, "🌿"),
    (200, "🌳"),
]
EMOJI_TOP = "🍀"          # score > 200
ALL_TIER_EMOJIS = {"🪨", "🌱", "🌿", "🌳", "🍀"}


def score_to_emoji(score: int) -> str:
    for ceiling, emoji in EMOJI_TIERS:
        if score <= ceiling:
            return emoji
    return EMOJI_TOP


def apply_emoji_prefix(title: str, score: int) -> str:
    """Remove emoji antigo (se houver) e aplica o novo baseado no score."""
    new_emoji = score_to_emoji(score)
    stripped = title.strip()
    for ch in ALL_TIER_EMOJIS:
        if stripped.startswith(ch):
            stripped = stripped[len(ch):].lstrip()
            break
    return f"{new_emoji} {stripped}"


# =====================================================
# PREPARAÇÃO PARA DERIVADOS (v1.2)
# =====================================================

# SLA REAL DO PRIMEIRO CONTATO (atividade)
FIRST_ACTIVITY_SLA_BUCKETS_HOURS = [
    (1, 25),
    (4, 20),
    (8, 10),
    (24, 5),
    (9999, 0),
]

# CICLO TOTAL DO DEAL (criado → ganho/perda)
DEAL_CYCLE_BUCKETS_DAYS = [
    (7, 10),
    (21, 5),
    (60, 0),
    (9999, -10),
]

# ATIVIDADES (contagem total do deal — "Negócio - Total de atividades")
ACTIVITIES_COUNT_BUCKETS = [
    (0, -10),   # 0 atividades
    (1, 0),     # 1 atividade
    (3, 5),     # 2–3
    (5, 10),    # 4–5
    (10, 8),    # 6–10
    (9999, 4),  # 11+
]

# DDD (neutro por padrão, pronto para aprender)
DDD_SCORES_DEFAULT = 0
DDD_FAVORABLE = {}  # ex: {"11": 3, "21": 3}
DDD_UNFAVORABLE = {}  # ex: {"XX": -3}

'''
  ▗▅▅▖   
▄▛▘‾‾▝▜▄ 
█▖    ▗█   © 2026 Copyright
███▅▅███   Ir.On
██●█████ 
▜▛  █▜▛█   "Feito com muito carinho."
    █  ▀ 
    ▀    
'''
