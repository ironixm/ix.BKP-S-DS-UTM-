# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Deal Score – V1.0.0                            │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ dealscore/deal_score.py                        │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from dealscore.deal_score_rules import (
    DEAL_SCORE_FIELD_ID,
    RESET_STAGES,
    STAGE_SCORES,
    STAGE_CONTATO_1,
    CONTACT1_SLA_BUCKETS,
    FUNIL_SCORES,
    CARGO_SCORES,
    SEGMENTO_SCORES,
    FORMATO_VENDAS_SCORES,
    PLATAFORMA_SCORES,
    SITE_VALIDO_SCORES,
    EMAIL_VALIDO_SCORES,
    EMAIL_EMPRESARIAL_SCORES,
    PHONE_VALIDO_SCORES,
    QUESTIONARIO_SCORES,
    STAGNATION_BUCKETS_DAYS,
    STAGNATION_CAPS,
    ACTIVITIES_COUNT_BUCKETS,
)

from logger import log_event

# =========================
# CAMPOS (Pipedrive IDs)
# =========================

FIELD_IDS = {
    "cargo_person": "aed03a98b790d3b419adf11d8b9d96c672c08ed7",
    "segmento_person": "d2db59579b5f3065fbe7686fb490d7c75c4efc15",
    "formato_vendas_person": "9471ac49eee5f37ccb6acd3c8ff7d2b614f5e5ec",
    "plataforma_deal": "5ff9c8fc1932afd89f54459496f390ba65608df0",
    "site_valido_deal": "ecdd3753a4bd88306256abf7d095db37f09fb422",
    "questionario_deal": "f6cfb20b4bc351e2467941d36f772da7c8da9e31",
    "profundidade_funil_deal": "8ba3c6ef23c1678a96c41b51748a7a8bf6fda577",
}

# =========================
# Helpers
# =========================

def _parse_pd_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except Exception:
        return None


def _hours_between(a: datetime | None, b: datetime | None) -> float | None:
    if not a or not b:
        return None
    return (b - a).total_seconds() / 3600.0


def _days_between(a: datetime | None, b: datetime | None) -> float | None:
    if not a or not b:
        return None
    return (b - a).total_seconds() / 86400.0


def _bool_to_sim_na(v: bool) -> str:
    return "Sim" if v else "Não"


def _get(entity: Mapping[str, Any], field_id: str) -> Any:
    return entity.get(field_id)


# =========================
# Validators
# =========================

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FREE_EMAIL_DOMAINS_RE = re.compile(
    r"@(gmail\.com|hotmail\.com|outlook\.com|live\.com|yahoo\.com(\.br)?|icloud\.com)$",
    re.I,
)


def is_valid_email(email: str | None) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def is_business_email(email: str | None) -> bool:
    return is_valid_email(email) and not FREE_EMAIL_DOMAINS_RE.search(email or "")


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D+", "", phone)
    return digits if len(digits) >= 10 else None


def is_valid_phone(phone: str | None) -> bool:
    return normalize_phone(phone) is not None


# =========================
# Scoring
# =========================

@dataclass
class ScoreBreakdown:
    total: int
    parts: dict[str, int]


def _score_bucket(value: float, buckets: list[tuple[float, int]]) -> int:
    for max_v, pts in buckets:
        if value <= max_v:
            return pts
    return buckets[-1][1]


def score_first_contact_sla(deal: Mapping[str, Any]) -> int:
    """
    SLA do primeiro contato: add_time → primeiro movimento real.
    Prioridade: first_activity_time > update_time (fallback defensivo).
    """
    add_dt = _parse_pd_dt(deal.get("add_time"))
    activity_dt = _parse_pd_dt(deal.get("first_activity_time"))
    ref_dt = activity_dt or _parse_pd_dt(deal.get("update_time"))

    hours = _hours_between(add_dt, ref_dt)
    if hours is None:
        return 0

    return _score_bucket(hours, CONTACT1_SLA_BUCKETS)


def score_stage(deal: Mapping[str, Any]) -> int:
    stage = deal.get("stage_id")
    if not isinstance(stage, int):
        return 0

    if stage in RESET_STAGES:
        return 0

    if stage == STAGE_CONTATO_1:
        return score_first_contact_sla(deal)

    return int(STAGE_SCORES.get(stage, 0))


def score_funil(deal: Mapping[str, Any], field_ids: Mapping[str, str]) -> int:
    raw = _get(deal, field_ids["profundidade_funil_deal"])
    if not isinstance(raw, str):
        return 0

    raw = raw.strip()

    # 1) KTL com marcador (K)/(L)/(T) → TOFU
    if "KTL" in raw and any(m in raw for m in ("(K)", "(L)", "(T)")):
        return FUNIL_SCORES["TOFU"]

    # 2) Prefixo oficial
    if raw.startswith("ix.T"):
        return FUNIL_SCORES["TOFU"]
    if raw.startswith("ix.M"):
        return FUNIL_SCORES["MOFU"]
    if raw.startswith("ix.B"):       # doc: ix.B → BOFU
        return FUNIL_SCORES["BOFU"]

    # 3) Fallback F1/F2/F3
    if "-F1" in raw or ".F1" in raw:
        return FUNIL_SCORES["TOFU"]
    if "-F2" in raw or ".F2" in raw:
        return FUNIL_SCORES["MOFU"]
    if "-F3" in raw or ".F3" in raw:
        return FUNIL_SCORES["BOFU"]

    return 0


def score_activities(deal: Mapping[str, Any]) -> int:
    """Contagem total de atividades do deal — proxy de engajamento real."""
    try:
        count = int(deal.get("activities_count") or 0)
    except Exception:
        return 0
    return _score_bucket(count, ACTIVITIES_COUNT_BUCKETS)


def _compute_dias_sem_movimento(deal: Mapping[str, Any], now: datetime) -> float | None:
    """
    Movimento real = max(last_activity_time, stage_change_time).
    Fallback defensivo: update_time (se ambos ausentes).
    """
    last_activity = _parse_pd_dt(deal.get("last_activity_time"))
    last_stage_change = _parse_pd_dt(deal.get("stage_change_time"))

    candidates = [t for t in [last_activity, last_stage_change] if t is not None]
    if candidates:
        last_movement = max(candidates)
    else:
        last_movement = _parse_pd_dt(deal.get("update_time"))

    return _days_between(last_movement, now)


def score_stagnation(deal: Mapping[str, Any], now: datetime) -> int:
    dias = _compute_dias_sem_movimento(deal, now)
    if dias is None:
        return 0
    return _score_bucket(dias, STAGNATION_BUCKETS_DAYS)


# =========================
# Main
# =========================

def compute_deal_score(
    deal: Mapping[str, Any],
    person: Mapping[str, Any] | None,
    field_ids: Mapping[str, str],
) -> ScoreBreakdown:
    now = datetime.now(timezone.utc)
    person = person or {}

    stage = deal.get("stage_id")

    # Override: Perdido → sempre -100
    if deal.get("status") == "lost":
        log_event("deal_score_override", {"deal_id": deal.get("id"), "reason": "lost"})
        return ScoreBreakdown(total=-100, parts={"status_perdido": -100})

    # Override: Quarentena → sempre +5
    if isinstance(stage, int) and stage in RESET_STAGES:
        log_event("deal_score_override", {"deal_id": deal.get("id"), "reason": "quarentena", "stage_id": stage})
        return ScoreBreakdown(total=5, parts={"quarentena": 5})

    parts: dict[str, int] = {}

    parts["stage"] = score_stage(deal)
    parts["funil"] = score_funil(deal, field_ids)
    parts["activities"] = score_activities(deal)

    parts["cargo"] = int(CARGO_SCORES.get(_get(person, field_ids["cargo_person"]), 0))
    parts["segmento"] = int(SEGMENTO_SCORES.get(_get(person, field_ids["segmento_person"]), 0))
    parts["formato_vendas"] = int(
        FORMATO_VENDAS_SCORES.get(_get(person, field_ids["formato_vendas_person"]), 0)
    )

    parts["plataforma"] = int(PLATAFORMA_SCORES.get(_get(deal, field_ids["plataforma_deal"]), 0))
    parts["site"] = int(SITE_VALIDO_SCORES.get(_get(deal, field_ids["site_valido_deal"]), 0))
    parts["questionario"] = int(QUESTIONARIO_SCORES.get(_get(deal, field_ids["questionario_deal"]), 0))

    def _extract_pd_value(field: Any) -> str | None:
        if isinstance(field, list) and field:
            v = field[0]
            return v.get("value") if isinstance(v, dict) else None
        if isinstance(field, dict):
            return field.get("value")
        return None

    email = _extract_pd_value(person.get("email"))
    phone = _extract_pd_value(person.get("phone"))

    parts["email"] = EMAIL_VALIDO_SCORES[_bool_to_sim_na(is_valid_email(email))]
    parts["email_empresarial"] = EMAIL_EMPRESARIAL_SCORES[_bool_to_sim_na(is_business_email(email))]
    parts["phone"] = PHONE_VALIDO_SCORES[_bool_to_sim_na(is_valid_phone(phone))]

    parts["stagnation"] = score_stagnation(deal, now)

    # Camada de prioridade do cliente (pesos altos, configuráveis via ENV)
    try:
        from dealscore.client_priority import compute_client_priority
        parts.update(compute_client_priority(deal, person))
    except Exception as exc:
        log_event("client_priority_error", {"deal_id": deal.get("id"), "error": str(exc)})

    total = max(-100, min(300, int(sum(parts.values()))))

    # Caps anti-ilusão: deals parados não podem ter score alto
    dias = _compute_dias_sem_movimento(deal, now)
    if dias is not None:
        for min_days, cap in STAGNATION_CAPS:
            if dias >= min_days:
                total = min(total, cap)
                break

    return ScoreBreakdown(total=total, parts=parts)


def build_dealscore_payload(score: int) -> dict:
    return {DEAL_SCORE_FIELD_ID: score}

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
