#!/usr/bin/env python3
# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Build Deals Analysis Db – V1.0.0               │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:56         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/build_deals_analysis_db.py             │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

from __future__ import annotations

import argparse
import re
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# CSV -> SQLite ingestion + derived fields + baseline score re-simulation.
# This is an analysis helper; it does NOT change production rules.
# -----------------------------------------------------------------------------


DATE_COLS = [
    "Negócio - Atualizado em",
    "Negócio - Negócio criado em",
    "Negócio - Data da última atividade",
    "Negócio - Última alteração de etapa",
    "Negócio - Ganho em",
    "Negócio - Negócio fechado em",
    "Negócio - Data de perda",
    "Negócio - Data de fechamento esperada",
]


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FREE_EMAIL_DOMAINS_RE = re.compile(
    r"@(gmail\.com|hotmail\.com|outlook\.com|live\.com|yahoo\.com(\.br)?|icloud\.com)$",
    re.I,
)
PHONE_DIGITS_RE = re.compile(r"\D+")


EMAIL_COLS = [
    "Pessoa - E-mail - Trabalho",
    "Pessoa - E-mail - Residencial",
    "Pessoa - E-mail - Outros",
]
PHONE_COLS = [
    "Pessoa - Telefone - Trabalho",
    "Pessoa - Telefone - Residencial",
    "Pessoa - Telefone - Celular",
    "Pessoa - Telefone - Outros",
    "Organização - Telefone",
]
SITE_COLS = [
    "Negócio - Site",
    "Organização - Website",
    "Organização - Site",
    "Organização - Site do indicado",
]


FUNIL_SCORES = {"TOFU": 5, "MOFU": 15, "BOFU": 30}


# Mirrors current rules (dealscore/deal_score_rules.py) but keyed by CSV stage labels.
STAGE_SCORES = {
    "Levantadas de Mão": 10,
    "Contato 02": -5,
    "Contato 03": -10,
    "Contato 04": -20,
    "Agendado": 30,
    "Dem. + Proposta": 60,
    "Em negociação": 120,
    "Leads RD Summit 2025": 5,
}

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

FORMATO_VENDAS_SCORES = {
    "Planos/assinaturas/mensalidades": 15,
    "E-commerce": 8,
    "Consultivo": 12,
    "consultivo": 12,
    "Lançamento de Infoprodutos": 5,
    "Outros": 0,
}

PLATAFORMA_SCORES = {"Hotmart": 6, "Eduzz": 5, "Sympla": 2, "Outros": 0}

SITE_VALIDO_SCORES = {"Sim": 15, "Não": -15}
EMAIL_VALIDO_SCORES = {"Sim": 10, "Não": -10}
EMAIL_EMPRESARIAL_SCORES = {"Sim": 10, "Não": 0}
PHONE_VALIDO_SCORES = {"Sim": 10, "Não": -5}
QUESTIONARIO_SCORES = {"Sim": 20, "Não": 0}

PROBABILITY_MAX_POINTS = 50
STAGNATION_BUCKETS_DAYS = [(1, 0), (3, -5), (7, -10), (14, -20), (9999, -40)]


def _score_bucket(value: int, buckets: list[tuple[int, int]]) -> int:
    for max_v, pts in buckets:
        if value <= max_v:
            return pts
    return buckets[-1][1]


def _extract_email(row: pd.Series) -> str | None:
    for c in EMAIL_COLS:
        v = row.get(c)
        if isinstance(v, str) and EMAIL_RE.match(v.strip()):
            return v.strip()
    return None


def _is_business_email(email: str | None) -> bool:
    return bool(email and not FREE_EMAIL_DOMAINS_RE.search(email))


def _extract_phone_digits(row: pd.Series) -> str | None:
    for c in PHONE_COLS:
        v = row.get(c)
        if isinstance(v, str) and v.strip():
            digits = PHONE_DIGITS_RE.sub("", v)
            if len(digits) >= 10:
                return digits
        elif pd.notna(v):
            digits = PHONE_DIGITS_RE.sub("", str(v))
            if len(digits) >= 10:
                return digits
    return None


def _has_valid_site(row: pd.Series) -> bool:
    for c in SITE_COLS:
        v = row.get(c)
        if isinstance(v, str) and v.strip() and "." in v:
            return True
    return False


def _score_contato01_sla(
    created_dt: pd.Timestamp | None, ref_dt: pd.Timestamp | None
) -> int:
    if pd.isna(created_dt) or pd.isna(ref_dt):
        return 0
    hours = (ref_dt - created_dt).total_seconds() / 3600.0
    # Mirrors dealscore/deal_score.py (Contato 01 SLA)
    if hours <= 1:
        return 30
    if hours <= 4:
        return 20
    if hours <= 8:
        return 10
    if hours <= 24:
        return 5
    return 0


@dataclass(frozen=True)
class FunilVirtualV2:
    label: str | None
    points: int
    flag_ktl: int


def compute_funil_virtual_v2(campanha: str | None) -> FunilVirtualV2:
    """
    Precedence (per latest decision):
    1) contains 'KTL' + '(K|L|T)' => TOFU
    2) startswith ix.T => TOFU
    3) startswith ix.M => MOFU
    4) startswith ix.B => BOFU
    5) fallback contains -F1/.F1 => TOFU, -F2/.F2 => MOFU, -F3/.F3 => BOFU
    """
    s = (campanha or "").strip()
    u = s.upper()

    flag_ktl = int(("KTL" in u) and bool(re.search(r"\((K|L|T)\)", s, re.I)))
    if flag_ktl:
        return FunilVirtualV2("TOFU", FUNIL_SCORES["TOFU"], flag_ktl)

    if u.startswith("IX.T"):
        return FunilVirtualV2("TOFU", FUNIL_SCORES["TOFU"], flag_ktl)
    if u.startswith("IX.M"):
        return FunilVirtualV2("MOFU", FUNIL_SCORES["MOFU"], flag_ktl)
    if u.startswith("IX.B"):
        return FunilVirtualV2("BOFU", FUNIL_SCORES["BOFU"], flag_ktl)

    if re.search(r"(-F3|\.F3)", u):
        return FunilVirtualV2("BOFU", FUNIL_SCORES["BOFU"], flag_ktl)
    if re.search(r"(-F2|\.F2)", u):
        return FunilVirtualV2("MOFU", FUNIL_SCORES["MOFU"], flag_ktl)
    if re.search(r"(-F1|\.F1)", u):
        return FunilVirtualV2("TOFU", FUNIL_SCORES["TOFU"], flag_ktl)

    return FunilVirtualV2(None, 0, flag_ktl)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="_docs/deals/deals-3157616-575.csv")
    ap.add_argument("--db", default="deals_analysis.db")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)

    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    now = pd.Timestamp.now()

    created = df.get("Negócio - Negócio criado em")
    last_activity = df.get("Negócio - Data da última atividade")
    last_update = df.get("Negócio - Atualizado em")
    last_stage_change = df.get("Negócio - Última alteração de etapa")

    if created is not None:
        df["idade_do_deal_dias"] = (now - created).dt.days
    else:
        df["idade_do_deal_dias"] = np.nan

    if last_activity is not None:
        last_activity_filled = last_activity.fillna(last_update)
        df["dias_sem_atividade"] = (now - last_activity_filled).dt.days
    else:
        df["dias_sem_atividade"] = np.nan

    if last_stage_change is not None:
        df["dias_sem_mudanca_etapa"] = (now - last_stage_change).dt.days
    else:
        df["dias_sem_mudanca_etapa"] = np.nan

    if "Negócio - Etapa" in df.columns:
        df["estagio_normalizado"] = (
            df["Negócio - Etapa"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
        )
    else:
        df["estagio_normalizado"] = np.nan

    # Values
    for col in [
        "Negócio - Valor",
        "Negócio - Valor de produtos",
        "Negócio - MRR",
        "Negócio - ARR",
        "Negócio - ACV",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    valor = df.get("Negócio - Valor")
    valor_prod = df.get("Negócio - Valor de produtos")
    if valor is not None and valor_prod is not None:
        valor_total = valor_prod.where(~valor_prod.isna(), valor)
        valor_total = np.where(
            ~valor_prod.isna() & ~valor.isna(),
            np.maximum(valor_prod, valor),
            valor_total,
        )
        df["valor_total_declarado"] = valor_total
        df["presenca_de_produtos"] = np.where(valor_prod.fillna(0) > 0, 1, 0)
    else:
        df["valor_total_declarado"] = np.nan
        df["presenca_de_produtos"] = 0

    # Existing stored score (if present)
    if "Negócio - ix.DealScore" in df.columns:
        df["score_atual"] = pd.to_numeric(df["Negócio - ix.DealScore"], errors="coerce")
    else:
        df["score_atual"] = np.nan

    # Funil virtual v2 + campaign flags
    campanha = (
        df.get("Negócio - Campanha", pd.Series([""] * len(df)))
        .fillna("")
        .astype(str)
    )
    df["flag_campanha_template"] = np.where(
        campanha.str.contains(r"\{\{.*\}\}", regex=True), 1, 0
    )

    funil_labels: list[str | None] = []
    funil_points: list[int] = []
    funil_ktl_flags: list[int] = []
    for v in campanha.tolist():
        fv = compute_funil_virtual_v2(v)
        funil_labels.append(fv.label)
        funil_points.append(fv.points)
        funil_ktl_flags.append(fv.flag_ktl)
    df["funil_virtual_v2"] = funil_labels
    df["funil_virtual_v2_pontos"] = funil_points
    df["flag_funil_ktl"] = funil_ktl_flags

    # Quality flags
    valid_email = []
    valid_phone = []
    valid_site = []
    for _, row in df.iterrows():
        email = _extract_email(row)
        phone_digits = _extract_phone_digits(row)
        valid_email.append(int(email is not None))
        valid_phone.append(int(phone_digits is not None))
        valid_site.append(int(_has_valid_site(row)))

    df["flag_dados_ruins"] = np.where(
        (pd.Series(valid_email) == 0)
        | (pd.Series(valid_phone) == 0)
        | (pd.Series(valid_site) == 0),
        1,
        0,
    )

    # Risk flags
    df["flag_parado"] = np.where(
        pd.to_numeric(df["dias_sem_atividade"], errors="coerce") >= 14, 1, 0
    )
    df["flag_regressao"] = np.where(
        pd.to_numeric(df["dias_sem_mudanca_etapa"], errors="coerce") >= 21, 1, 0
    )

    # -------------------------------------------------------------------------
    # Approximate current DealScore calc from the CSV (for analysis/simulation)
    # -------------------------------------------------------------------------
    part_stage: list[int] = []
    part_funil: list[int] = []
    part_cargo: list[int] = []
    part_segmento: list[int] = []
    part_formato: list[int] = []
    part_plataforma: list[int] = []
    part_site: list[int] = []
    part_questionario: list[int] = []
    part_email: list[int] = []
    part_email_emp: list[int] = []
    part_phone: list[int] = []
    part_probability: list[int] = []
    part_status: list[int] = []
    part_stagnation: list[int] = []
    total_score: list[int] = []

    for _, row in df.iterrows():
        etapa = row.get("Negócio - Etapa")

        if etapa == "Quarentena":
            stg = 0
            fun_pts = 0
            cargo_pts = 0
            seg_pts = 0
            formato_pts = 0
            plataforma_pts = 0
            site_pts = 0
            quest_pts = 0
            email_pts = 0
            email_emp_pts = 0
            phone_pts = 0
            prob_pts = 0
            status_pts = 0
            stagn_pts = 0
            tot = 0
        else:
            # Stage
            if etapa == "Contato 01":
                created_dt = row.get("Negócio - Negócio criado em")
                ref_dt = row.get("Negócio - Data da última atividade")
                if pd.isna(ref_dt):
                    ref_dt = row.get("Negócio - Atualizado em")
                stg = _score_contato01_sla(created_dt, ref_dt)
            else:
                stg = int(STAGE_SCORES.get(etapa, 0))

            # Funil (as-is in production code today): startswith ix.T / ix.M / ix.F
            raw_funil = row.get("Negócio - Campanha")
            fun_pts = 0
            if isinstance(raw_funil, str):
                rf = raw_funil.strip()
                if rf.startswith("ix.T"):
                    fun_pts = FUNIL_SCORES["TOFU"]
                elif rf.startswith("ix.M"):
                    fun_pts = FUNIL_SCORES["MOFU"]
                elif rf.startswith("ix.F"):
                    fun_pts = FUNIL_SCORES["BOFU"]

            cargo_pts = int(CARGO_SCORES.get(row.get("Pessoa - Cargo"), 0))
            seg_pts = int(SEGMENTO_SCORES.get(row.get("Pessoa - Segmento"), 0))
            formato_pts = int(
                FORMATO_VENDAS_SCORES.get(row.get("Pessoa - Formato de vendas"), 0)
            )
            plataforma_pts = int(
                PLATAFORMA_SCORES.get(row.get("Negócio - Plataforma de vendas"), 0)
            )

            site_valid = "Sim" if _has_valid_site(row) else "Não"
            site_pts = int(SITE_VALIDO_SCORES.get(site_valid, 0))

            q = row.get("Negócio - Preencheu o questionário?")
            if isinstance(q, str):
                q = q.strip().capitalize()
            quest_pts = int(QUESTIONARIO_SCORES.get(q, 0))

            email = _extract_email(row)
            email_pts = int(EMAIL_VALIDO_SCORES["Sim" if email else "Não"])
            email_emp_pts = int(
                EMAIL_EMPRESARIAL_SCORES["Sim" if _is_business_email(email) else "Não"]
            )

            phone_digits = _extract_phone_digits(row)
            phone_pts = int(PHONE_VALIDO_SCORES["Sim" if phone_digits else "Não"])

            try:
                p = int(row.get("Negócio - Probabilidade") or 0)
            except Exception:
                p = 0
            p = max(0, min(100, p))
            prob_pts = int((p / 100.0) * PROBABILITY_MAX_POINTS)

            s = row.get("Negócio - Status")
            s_norm = s.strip().lower() if isinstance(s, str) else ""
            status_pts = -100 if s_norm in ("lost", "perdido") else 0

            upd = row.get("Negócio - Atualizado em")
            if pd.notna(upd):
                d = int((now - upd).days)
                stagn_pts = int(_score_bucket(d, STAGNATION_BUCKETS_DAYS))
            else:
                stagn_pts = 0

            tot = (
                stg
                + fun_pts
                + cargo_pts
                + seg_pts
                + formato_pts
                + plataforma_pts
                + site_pts
                + quest_pts
                + email_pts
                + email_emp_pts
                + phone_pts
                + prob_pts
                + status_pts
                + stagn_pts
            )
            tot = int(np.clip(tot, -100, 300))

        part_stage.append(int(stg))
        part_funil.append(int(fun_pts))
        part_cargo.append(int(cargo_pts))
        part_segmento.append(int(seg_pts))
        part_formato.append(int(formato_pts))
        part_plataforma.append(int(plataforma_pts))
        part_site.append(int(site_pts))
        part_questionario.append(int(quest_pts))
        part_email.append(int(email_pts))
        part_email_emp.append(int(email_emp_pts))
        part_phone.append(int(phone_pts))
        part_probability.append(int(prob_pts))
        part_status.append(int(status_pts))
        part_stagnation.append(int(stagn_pts))
        total_score.append(int(tot))

    df["part_stage"] = part_stage
    df["part_funil"] = part_funil
    df["part_cargo"] = part_cargo
    df["part_segmento"] = part_segmento
    df["part_formato_vendas"] = part_formato
    df["part_plataforma"] = part_plataforma
    df["part_site"] = part_site
    df["part_questionario"] = part_questionario
    df["part_email"] = part_email
    df["part_email_empresarial"] = part_email_emp
    df["part_phone"] = part_phone
    df["part_probability"] = part_probability
    df["part_status"] = part_status
    df["part_stagnation"] = part_stagnation
    df["score_calculado_atual"] = total_score

    conn = sqlite3.connect(args.db)
    df.to_sql("deals", conn, if_exists="replace", index=False)
    conn.close()

    status_counts = (
        df.get("Negócio - Status", pd.Series(dtype=object))
        .value_counts(dropna=False)
        .to_dict()
    )
    funil_counts = pd.Series(funil_labels).value_counts(dropna=False).to_dict()

    print("SQLite criado/atualizado:", args.db)
    print("rows:", len(df), "cols:", len(df.columns))
    print("status_counts:", status_counts)
    print("funil_virtual_v2_counts:", funil_counts)


if __name__ == "__main__":
    main()

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
