"""
Camada CLIENT PRIORITY — espelha os 9 critérios definidos pelo cliente
(planilha enviada em 2026-04-23) com pesos *2x* maiores que os
originais para garantir prioridade superior aos demais sinais.

Critérios do cliente (peso máx original → escalado 2x):
    1. Lead Indicado          +30 → +60   (Sim)
    2. CRM Preferencial       +20 → +40   (Sim)
    3. Qtd Pessoas no MKT     +20 → +40   (1=4, 2=8, 3=12, 4=16, 5=20, 7=28, 10=36, 15=40)
    4. Dias para Agendar      +20 → +40   (≤1d:40, ≤3d:30, ≤7d:20, ≤14d:10, >14d:0)
    5. Segmento (cliente)     +10 → +20   (Tec/Edu=20, Saúde=14, Energia/Imob/Cons/Fin=10, Cont=2, Outros=0)
    6. Qtd Pessoas Comercial  +10 → +20   (mesma escala do MKT escalada)
    7. Valores OK?            -20 → -40   (penaliza só se "Não"; Sim=0)
    8. Plataforma Integrada   -10 → -20   (penaliza só se "Não")
    9. Cargo Decisor          -10 → -20   (penaliza só se "Não")

Ajustes possíveis sem redeploy: cada peso máximo é ENV var.

Field IDs custom do Pipedrive: como não conhecemos todos os IDs ainda,
os campos novos são configuráveis via ENV. Se vazio, o critério vira no-op
(sinalizado nos logs como `client_priority_field_missing`).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Mapping

from logger import log_event


# =====================================================
# CONFIG (todos overridable via ENV)
# =====================================================

def _envi(key: str, default: int) -> int:
    try: return int(os.environ.get(key, default))
    except (TypeError, ValueError): return default


WEIGHTS = {
    "lead_indicado":      _envi("CLIENT_W_LEAD_INDICADO", 60),
    "crm_preferencial":   _envi("CLIENT_W_CRM_PREFERENCIAL", 40),
    "pessoas_mkt_max":    _envi("CLIENT_W_PESSOAS_MKT", 40),
    "dias_agendar_max":   _envi("CLIENT_W_DIAS_AGENDAR", 40),
    "segmento_max":       _envi("CLIENT_W_SEGMENTO", 20),
    "pessoas_com_max":    _envi("CLIENT_W_PESSOAS_COMERCIAL", 20),
    "valores_nao_ok":     _envi("CLIENT_W_VALORES_NAO_OK", -40),
    "plataforma_nao_ok":  _envi("CLIENT_W_PLATAFORMA_NAO_OK", -20),
    "cargo_nao_decisor":  _envi("CLIENT_W_CARGO_NAO_DECISOR", -20),
}


# Field IDs custom do Pipedrive (Grupo "Deal Score", criados em 2026-04-27).
# Todos overridable via ENV. Vazio = critério ignorado (no-op).
FIELDS = {
    "lead_indicado":      os.environ.get("CLIENT_FIELD_LEAD_INDICADO",        "cca13a8431980119ea79b10b745f6eafb7f66506"),
    "crm_preferencial":   os.environ.get("CLIENT_FIELD_CRM_PREFERENCIAL",     "3fee6fc3cf73878c5ea55168f47b46b8370349e2"),
    "pessoas_mkt":        os.environ.get("CLIENT_FIELD_PESSOAS_MKT",          "ae03b4b2a11bdcd8f311e1d356583ef5aff5fcb0"),
    "pessoas_com":        os.environ.get("CLIENT_FIELD_PESSOAS_COMERCIAL",    "c15384a2cb1d0016846cf7f8841181a4854f2658"),
    "valores_ok":         os.environ.get("CLIENT_FIELD_VALORES_OK",           "646c1f673dab3f44faf5c363e3a32e2a6a17927a"),
    "plataforma_integrada": os.environ.get("CLIENT_FIELD_PLATAFORMA_INTEGRADA","066c89ea3a1b2900e24e1025ebf0768abba98c8c"),
    "cargo_decisor":      os.environ.get("CLIENT_FIELD_CARGO_DECISOR",        "5d55571434b914b54bb2c1b11fe18c5be1b0034e"),
    "dias_agendar":       os.environ.get("CLIENT_FIELD_DIAS_AGENDAR",         "0c17c7c2f3ef647a768f8fb5aa00a87a0d2a3568"),
}

# Mapping option_id (Pipedrive enum) → label semântico
OPTION_LABELS = {
    # Lead indicado?
    "296": "Sim", "297": "Não",
    # CRM Preferencial?
    "298": "Sim", "318": "Não",
    # Plataforma Integrada?
    "314": "Sim", "317": "Não",
    # Os valores estão OK?
    "313": "Sim",
    # Cargo Decisor?
    "315": "Sim", "316": "Não",
    # Qtd MKT (1-10)
    "299": "1","300":"2","301":"3","302":"4","303":"5","304":"7","305":"10",
    # Qtd Comercial (1-10)
    "306":"1","307":"2","308":"3","309":"4","310":"5","311":"7","312":"10",
}

# Reverso: label → option_id (para escrever via API)
OPTION_IDS_MKT = {"1":"299","2":"300","3":"301","4":"302","5":"303","7":"304","10":"305"}
OPTION_IDS_COM = {"1":"306","2":"307","3":"308","4":"309","5":"310","7":"311","10":"312"}

def headcount_bucket(qtd: int) -> str:
    """Mapeia headcount inferido para o bucket disponível no campo (1,2,3,4,5,7,10)."""
    for b in (1,2,3,4,5,7,10):
        if qtd <= b: return str(b)
    return "10"

# Reusa fields já mapeados:
SEGMENTO_FIELD_ID = "d2db59579b5f3065fbe7686fb490d7c75c4efc15"  # person
CARGO_FIELD_ID    = "aed03a98b790d3b419adf11d8b9d96c672c08ed7"  # person
PERSON_CRM_FIELD  = "d0f212a3d4b13b7aee6f943439b06a46fa8f2de3"  # person.CRM (varchar)
DEAL_FONTE_KEY    = "81701fa45b2f46b8f081320b73741d3232fbf95a"  # deal (fallback p/ Lead Indicado)

# CRM weights — calibrados a partir de win-rate último ano (2026-04-29).
# Baseline (vazio) = 25.6% win rate. Pesos relativos ao baseline.
CRM_WEIGHTS = {
    "pipedrive": 50,    # win 36% + cliente prefere
    "hubspot":   40,    # win 35%
    "moskit":    30,    # cliente prioriza (n pequeno)
    "rdstation": 25,
    "agendor":   25,
    "salesforce":20,
    "kommo":     20,
    "zoho":      15,
    "bitrix":    10,
    "ploomes":   10,
    "fleeg":     10,
    "meetz":     10,
    "outro":     20,    # qualquer string ≠ vazio/planilha/whatsapp/sem
    "planilha":  -10,   # diz que usa planilha/excel
    "whatsapp":  -10,
    "sem_crm":   -20,   # afirmou explicitamente "sem CRM"
    "vazio":     -10,   # campo vazio (default)
}

def _normalize_crm(raw: Any) -> str:
    s = (raw or "")
    if not isinstance(s, str): s = str(s)
    cl = s.strip().lower()
    if not cl: return "vazio"
    if "pipedrive" in cl or "pipe drive" in cl: return "pipedrive"
    if "hubspot" in cl or "hub spot" in cl:     return "hubspot"
    if "moskit" in cl: return "moskit"
    if "rdstation" in cl or "rd station" in cl or "rd crm" in cl or cl=="rd": return "rdstation"
    if "agendor" in cl: return "agendor"
    if "ploomes" in cl: return "ploomes"
    if "salesforce" in cl: return "salesforce"
    if "bitrix" in cl: return "bitrix"
    if "zoho" in cl: return "zoho"
    if "kommo" in cl or "amocrm" in cl: return "kommo"
    if "fleeg" in cl: return "fleeg"
    if "meetz" in cl or "meets" in cl: return "meetz"
    if "planilha" in cl or "excel" in cl or "sheet" in cl: return "planilha"
    if "whats" in cl or "wapp" in cl: return "whatsapp"
    if any(w in cl for w in ("nao tem", "não tem", "nenhum", "sem crm", "n/a")) and len(cl) < 30:
        return "sem_crm"
    return "outro"

def crm_weight(raw: Any) -> int:
    return CRM_WEIGHTS.get(_normalize_crm(raw), 0)

# Stages
STAGE_AGENDADO = 47

# =====================================================
# Mappings derivados do anexo do cliente
# =====================================================

# Segmento — pesos relativos (cliente) escalados ao máx 20.
# (Cliente: Tec=10, Edu=10, Saúde=7, Energia=5, Imob=5, Cons=5, Fin=5, Cont=1, Outros=0)
_CLIENT_SEGMENTO_RAW = {
    "Tecnologia": 10, "Tecnologia/Software/SaaS": 10,
    "Educação": 10,
    "Telecom": 8, "Internet e Telefonia": 8,
    "Saúde": 7, "Saúde e bem estar": 7,
    "Consórcio": 5,
    "Energia solar": 5,
    "Incorporação/Imobiliária": 5,
    "Financeiros/Crédito": 5, "Seguros": 5, "Corretoras e seguradoras": 5,
    "Contabilidade": 1,
}
_SCALE_SEG = WEIGHTS["segmento_max"] / 10
SEGMENTO_CLIENT_SCORES = {k: round(v * _SCALE_SEG) for k, v in _CLIENT_SEGMENTO_RAW.items()}

# Pessoas (MKT/Comercial) — escala 1=4, 2=8, ... 15=40 (linear até cap)
def _pessoas_score(qtd: int, max_pts: int) -> int:
    if qtd <= 0: return 0
    # Pontos = min(qtd * (max_pts/15), max_pts)
    return int(min(qtd * (max_pts / 15.0), max_pts))


# Dias para agendar
DIAS_AGENDAR_BUCKETS = [
    (1, 1.00),    # ≤ 1d → 100% do peso
    (3, 0.75),    # ≤ 3d → 75%
    (7, 0.50),    # ≤ 7d → 50%
    (14, 0.25),   # ≤ 14d → 25%
    (9999, 0.0),
]


# Cargos considerados DECISOR (presença = neutro; ausência = penalidade)
CARGOS_DECISOR = {"CEO", "Dono/Proprietário(a)", "Diretor(a)", "Sócio(a)"}


# =====================================================
# Helpers
# =====================================================

def _parse_pd_dt(value):
    if not value: return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _is_yes(value: Any) -> bool | None:
    """Retorna True/False/None (None = campo ausente/desconhecido).
    Aceita também option_ids do Pipedrive via OPTION_LABELS."""
    if value is None or value == "": return None
    if isinstance(value, bool): return value
    s = str(value).strip()
    # Pipedrive enum: option_id numérico → label
    if s in OPTION_LABELS:
        s = OPTION_LABELS[s]
    sl = s.lower()
    if sl in ("sim", "yes", "true", "y"): return True
    if sl in ("não", "nao", "no", "false", "n"): return False
    if sl == "1": return True
    if sl == "0": return False
    return None


def _is_no(value: Any) -> bool:
    """Retorna True somente se valor explicitamente = Não."""
    return _is_yes(value) is False


def _get_int(d: Mapping, key: str) -> int | None:
    v = d.get(key) if key else None
    if v is None or v == "": return None
    s = str(v).strip()
    # option_id → label numérico
    if s in OPTION_LABELS:
        s = OPTION_LABELS[s]
    try: return int(float(s))
    except (TypeError, ValueError): return None


# =====================================================
# Compute
# =====================================================

def compute_client_priority(deal: Mapping[str, Any], person: Mapping[str, Any] | None) -> dict[str, int]:
    """
    Retorna dict de partes do score (apenas valores != 0 são incluídos).
    Não levanta exceção: critérios faltantes simplesmente não pontuam.
    """
    parts: dict[str, int] = {}
    person = person or {}

    # 1) Lead Indicado (+60 se Sim)
    if FIELDS["lead_indicado"]:
        v = _is_yes(deal.get(FIELDS["lead_indicado"]))
        if v is True:
            parts["client_lead_indicado"] = WEIGHTS["lead_indicado"]
    else:
        # Fallback: detecta "indicação" no campo Fonte
        fonte = (deal.get(DEAL_FONTE_KEY) or "")
        if isinstance(fonte, str) and "indica" in fonte.lower():
            parts["client_lead_indicado"] = WEIGHTS["lead_indicado"]

    # 2) CRM Preferencial — peso variável por CRM detectado em person.CRM.
    #    Se o campo "CRM Preferencial?" está marcado Sim → bônus fixo.
    #    Se vazio → infere via person.CRM (varchar) e aplica CRM_WEIGHTS.
    crm_pref_field = deal.get(FIELDS["crm_preferencial"]) if FIELDS["crm_preferencial"] else None
    if _is_yes(crm_pref_field) is True:
        parts["client_crm_preferencial"] = WEIGHTS["crm_preferencial"]
    elif _is_no(crm_pref_field):
        # cliente marcou explicitamente "Não" → -10
        parts["client_crm_preferencial"] = -10
    else:
        # Inferência via person.CRM
        crm_raw = person.get(PERSON_CRM_FIELD) if person else None
        w = crm_weight(crm_raw)
        if w:
            parts["client_crm_preferencial"] = w

    # 3) Qtd Pessoas no MKT (escala linear até +40)
    qtd_mkt = _get_int(deal, FIELDS["pessoas_mkt"]) or _get_int(person, FIELDS["pessoas_mkt"])
    if qtd_mkt is not None and qtd_mkt > 0:
        parts["client_pessoas_mkt"] = _pessoas_score(qtd_mkt, WEIGHTS["pessoas_mkt_max"])

    # 4) Dias para Agendar — prioriza valor manual no campo do cliente; senão calcula.
    dias = None
    if FIELDS["dias_agendar"]:
        dias_raw = deal.get(FIELDS["dias_agendar"])
        if dias_raw not in (None, ""):
            try: dias = float(dias_raw)
            except (TypeError, ValueError): dias = None
    if dias is None:
        add_dt = _parse_pd_dt(deal.get("add_time"))
        if add_dt and deal.get("stage_id") == STAGE_AGENDADO:
            ref_dt = _parse_pd_dt(deal.get("stage_change_time"))
            if ref_dt:
                dias = (ref_dt - add_dt).total_seconds() / 86400.0
    if dias is not None and dias >= 0:
        for cap, frac in DIAS_AGENDAR_BUCKETS:
            if dias <= cap:
                pts = int(round(WEIGHTS["dias_agendar_max"] * frac))
                if pts:
                    parts["client_dias_agendar"] = pts
                break

    # 5) Segmento (até +20)
    seg = person.get(SEGMENTO_FIELD_ID)
    if isinstance(seg, str) and seg in SEGMENTO_CLIENT_SCORES:
        pts = SEGMENTO_CLIENT_SCORES[seg]
        if pts:
            parts["client_segmento"] = pts

    # 6) Qtd Pessoas no Comercial (até +20)
    qtd_com = _get_int(deal, FIELDS["pessoas_com"]) or _get_int(person, FIELDS["pessoas_com"])
    if qtd_com is not None and qtd_com > 0:
        parts["client_pessoas_comercial"] = _pessoas_score(qtd_com, WEIGHTS["pessoas_com_max"])

    # 7) Valores OK? (penaliza -40 se Não; Sim/ausente = 0)
    if FIELDS["valores_ok"] and _is_no(deal.get(FIELDS["valores_ok"])):
        parts["client_valores_nao_ok"] = WEIGHTS["valores_nao_ok"]

    # 8) Plataforma Integrada (penaliza -20 se Não)
    if FIELDS["plataforma_integrada"] and _is_no(deal.get(FIELDS["plataforma_integrada"])):
        parts["client_plataforma_nao_integrada"] = WEIGHTS["plataforma_nao_ok"]

    # 9) Cargo Decisor — prioriza campo manual; senão deriva do cargo da pessoa.
    cargo_field_val = deal.get(FIELDS["cargo_decisor"]) if FIELDS["cargo_decisor"] else None
    cd = _is_yes(cargo_field_val)
    if cd is False:
        parts["client_cargo_nao_decisor"] = WEIGHTS["cargo_nao_decisor"]
    elif cd is None:
        cargo = person.get(CARGO_FIELD_ID)
        if isinstance(cargo, str) and cargo and cargo not in CARGOS_DECISOR:
            parts["client_cargo_nao_decisor"] = WEIGHTS["cargo_nao_decisor"]

    return parts
