#!/usr/bin/env python3
"""
Pré-preenchimento dos campos do grupo "Deal Score" do Pipedrive (criados em
2026-04-27) usando dados que já temos em outros campos.

CRÍTICO: nunca sobrescreve um campo que tenha sido editado manualmente por
um usuário humano. O guard usa `/deals/{id}/flow` e considera "manual"
qualquer mudança no campo cujo `user_id != BOT_USER_ID`.

Campos pré-preenchidos:
  - Lead indicado?       (opcao Sim/Não)  ← deriva de deal.Fonte contém "indica"
  - CRM Preferencial?    (opcao Sim/Não)  ← Sim se person.CRM preenchido com CRM real
  - Cargo Decisor?       (opcao Sim/Não)  ← Sim/Não a partir de person.Cargo
  - Plataforma Integrada?(opcao Sim/Não)  ← Sim se deal.PlataformaVendas preenchido
  - Qtd dias para agendar(double)         ← calcula add_time → stage_change(47)

Uso:
  python3 scripts/prefill_dealscore_fields.py --limit 200 --dry-run
  python3 scripts/prefill_dealscore_fields.py --limit 50
  python3 scripts/prefill_dealscore_fields.py --only lead_indicado,cargo_decisor

Variáveis de ambiente:
  PIPEDRIVE_API_KEY (obrigatório)
  BOT_USER_ID       (default: 3157616 - Roberta Torres)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

# garante import dos módulos do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dealscore.client_priority import (  # noqa: E402
    FIELDS, OPTION_LABELS, OPTION_IDS_MKT, OPTION_IDS_COM, CARGOS_DECISOR,
    CARGO_FIELD_ID, PERSON_CRM_FIELD, DEAL_FONTE_KEY, STAGE_AGENDADO,
    _normalize_crm, headcount_bucket,
)

API = "https://buzzlead.pipedrive.com/api/v1"
TOKEN = os.environ.get("PIPEDRIVE_API_KEY")
BOT_USER_ID = int(os.environ.get("BOT_USER_ID", "3157616"))
PD_PLATAFORMA_VENDAS = "5ff9c8fc1932afd89f54459496f390ba65608df0"  # deal.Plataforma de vendas

OPT_LEAD_SIM, OPT_LEAD_NAO     = "296", "297"
OPT_CRM_SIM,  OPT_CRM_NAO      = "298", "318"
OPT_PLAT_SIM, OPT_PLAT_NAO     = "314", "317"
OPT_CARGO_SIM,OPT_CARGO_NAO    = "315", "316"


def _req(method: str, path: str, payload: dict | None = None) -> dict:
    sep = "&" if "?" in path else "?"
    url = f"{API}{path}{sep}api_token={TOKEN}"
    data = None
    headers = {"User-Agent": "ix-blz-s prefill/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def list_deals(status: str = "open", limit: int = 200, start: int = 0):
    res = _req("GET", f"/deals?status={status}&limit={limit}&start={start}&sort=update_time%20DESC")
    return res.get("data") or [], res.get("additional_data", {}).get("pagination", {})


def get_person(pid: int) -> dict:
    if not pid: return {}
    try:
        return (_req("GET", f"/persons/{pid}").get("data") or {})
    except Exception:
        return {}


_field_change_cache: dict[int, set[str]] = {}


def manual_changed_fields(deal_id: int) -> set[str]:
    """Retorna set de field_keys que tiveram mudanças por user != bot."""
    if deal_id in _field_change_cache:
        return _field_change_cache[deal_id]
    manual: set[str] = set()
    try:
        res = _req("GET", f"/deals/{deal_id}/flow?limit=200&items=dealChange")
        for it in (res.get("data") or []):
            d = it.get("data") or {}
            uid = d.get("user_id")
            fk = d.get("field_key")
            if fk and uid and int(uid) != BOT_USER_ID:
                manual.add(fk)
    except Exception:
        pass
    _field_change_cache[deal_id] = manual
    return manual


def parse_dt(s):
    if not s: return None
    try: return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception: return None


def derive_values(deal: dict, person: dict, with_headcount: bool = False) -> dict[str, Any]:
    """Retorna {field_key: value_to_set} apenas para campos que podemos inferir
    e cujo valor atual está vazio."""
    out: dict[str, Any] = {}

    # 1) Lead indicado?
    fk = FIELDS["lead_indicado"]
    if fk and not deal.get(fk):
        fonte = deal.get(DEAL_FONTE_KEY) or ""
        if isinstance(fonte, str) and "indica" in fonte.lower():
            out[fk] = OPT_LEAD_SIM

    # 2) CRM Preferencial?
    fk = FIELDS["crm_preferencial"]
    if fk and not deal.get(fk):
        bucket = _normalize_crm(person.get(PERSON_CRM_FIELD))
        if bucket not in ("vazio", "sem_crm", "planilha", "whatsapp"):
            out[fk] = OPT_CRM_SIM
        elif bucket == "sem_crm":
            out[fk] = OPT_CRM_NAO

    # 3) Cargo Decisor?
    fk = FIELDS["cargo_decisor"]
    if fk and not deal.get(fk):
        cargo = person.get(CARGO_FIELD_ID)
        if isinstance(cargo, str) and cargo.strip():
            out[fk] = OPT_CARGO_SIM if cargo.strip() in CARGOS_DECISOR else OPT_CARGO_NAO

    # 4) Plataforma Integrada?
    fk = FIELDS["plataforma_integrada"]
    if fk and not deal.get(fk):
        plat = deal.get(PD_PLATAFORMA_VENDAS)
        if isinstance(plat, str) and plat.strip():
            out[fk] = OPT_PLAT_SIM

    # 5) Qtd dias para agendar
    fk = FIELDS["dias_agendar"]
    if fk and not deal.get(fk):
        add = parse_dt(deal.get("add_time"))
        if add and deal.get("stage_id") == STAGE_AGENDADO:
            ref = parse_dt(deal.get("stage_change_time"))
            if ref:
                d = (ref - add).total_seconds() / 86400.0
                if d >= 0:
                    out[fk] = round(d, 2)

    # 6+7) Headcount MKT/Comercial — heurística por valor do deal (opt-in)
    # Valor do deal aproxima tamanho do cliente. Conservador.
    if with_headcount:
        try:
            v = float(deal.get("value") or 0)
        except (TypeError, ValueError):
            v = 0
        if v <= 0:    qm, qc = 1, 1
        elif v < 2000:    qm, qc = 1, 1
        elif v < 10000:   qm, qc = 2, 2
        elif v < 50000:   qm, qc = 3, 3
        elif v < 200000:  qm, qc = 5, 5
        else:             qm, qc = 7, 7
        fk_m = FIELDS["pessoas_mkt"]
        if fk_m and not deal.get(fk_m):
            out[fk_m] = OPTION_IDS_MKT[headcount_bucket(qm)]
        fk_c = FIELDS["pessoas_com"]
        if fk_c and not deal.get(fk_c):
            out[fk_c] = OPTION_IDS_COM[headcount_bucket(qc)]

    return out


def process_one(deal: dict, dry_run: bool = False, with_headcount: bool = False,
                only_keys: set | None = None) -> dict:
    """Processa um único deal: respeita guard manual + retorna o que aconteceu.

    Retorna {"action": "updated|skip_empty|skip_manual|error", "payload": {...}}
    """
    pid_obj = deal.get("person_id") or {}
    pid = pid_obj.get("value") if isinstance(pid_obj, dict) else pid_obj
    person = get_person(pid) if pid else {}
    derived = derive_values(deal, person, with_headcount=with_headcount)
    if only_keys is not None:
        derived = {k: v for k, v in derived.items() if k in only_keys}
    if not derived:
        return {"action": "skip_empty", "payload": {}}
    try:
        manual = manual_changed_fields(deal["id"])
    except Exception:
        manual = set()
    payload = {k: v for k, v in derived.items() if k not in manual}
    if not payload:
        return {"action": "skip_manual", "payload": {}}
    if dry_run:
        return {"action": "updated", "payload": payload, "dry": True}
    try:
        _req("PUT", f"/deals/{deal['id']}", payload)
        return {"action": "updated", "payload": payload}
    except Exception as e:
        return {"action": "error", "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="Total de deals a processar")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--status", default="open", choices=("open", "all_not_deleted", "won", "lost"))
    ap.add_argument("--only", default="", help="csv de campos: lead_indicado,crm_preferencial,cargo_decisor,plataforma_integrada,dias_agendar")
    ap.add_argument("--with-headcount", action="store_true",
                    help="Inferir Qtd MKT/Comercial via heurística pelo valor do deal (conservador)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not TOKEN:
        sys.exit("PIPEDRIVE_API_KEY não setado")

    only_keys = None
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        only_keys = {FIELDS[k] for k in wanted if k in FIELDS}

    seen = updated = skipped_manual = skipped_empty = errors = 0
    start = 0
    while seen < args.limit:
        page_limit = min(args.page_size, args.limit - seen)
        deals, pag = list_deals(args.status, page_limit, start)
        if not deals: break
        for deal in deals:
            seen += 1
            pid_obj = deal.get("person_id") or {}
            pid = pid_obj.get("value") if isinstance(pid_obj, dict) else pid_obj
            person = get_person(pid)
            derived = derive_values(deal, person, with_headcount=args.with_headcount)
            if only_keys is not None:
                derived = {k: v for k, v in derived.items() if k in only_keys}
            if not derived:
                skipped_empty += 1
                continue
            manual = manual_changed_fields(deal["id"])
            payload = {k: v for k, v in derived.items() if k not in manual}
            if not payload:
                skipped_manual += 1
                continue
            if args.dry_run:
                print(f"[DRY] deal {deal['id']:>6} → {payload}")
                updated += 1
                continue
            try:
                _req("PUT", f"/deals/{deal['id']}", payload)
                updated += 1
                print(f"[OK]  deal {deal['id']:>6} → {payload}")
                time.sleep(0.15)  # ~6 req/s, abaixo de qualquer limite
            except Exception as e:
                errors += 1
                print(f"[ERR] deal {deal['id']:>6}: {e}")
        nxt = pag.get("next_start")
        if not nxt: break
        start = nxt

    print("\n=== resumo ===")
    print(f"  deals vistos:           {seen}")
    print(f"  atualizados:            {updated}")
    print(f"  skip (sem inferência):  {skipped_empty}")
    print(f"  skip (editado manual):  {skipped_manual}")
    print(f"  erros:                  {errors}")


if __name__ == "__main__":
    main()
