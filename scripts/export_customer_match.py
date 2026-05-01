#!/usr/bin/env python3
"""Exporta lista de clientes (deals WON) no formato Customer Match do Google Ads.

Saída: tmp/customer_match_won_<YYYYMMDD>.csv
Colunas: Email, First Name, Last Name, Country, Zip, Phone, LTV (extra)

Uso:
    PIPEDRIVE_API_KEY=xxx python3 scripts/export_customer_match.py [--limit N]

LTV: usa DEAL_LTV_KEY do deal se preenchido; senão calcula via compute_ltv(score).
Pessoas duplicadas (mesmo person_id) são consolidadas (LTV somado).
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pd_api import _request, get_person  # type: ignore
from mappings import DEAL_LTV_KEY  # type: ignore
from ltv import compute_ltv  # type: ignore

DEAL_SCORE_FIELD_ID = "6ecee6457426bc4cc8f2fcce89b14baf3793ecfe"
COUNTRY_DEFAULT = "BR"


def _norm(s):
    return (str(s).strip() if s is not None else "")


def _split_name(full: str) -> tuple[str, str]:
    parts = (full or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _phone_e164(raw: str, default_cc: str = "55") -> str:
    if not raw:
        return ""
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return ""
    if raw.strip().startswith("+"):
        return "+" + digits
    if digits.startswith(default_cc):
        return "+" + digits
    return "+" + default_cc + digits


def _extract_person(person: dict) -> dict:
    if not person:
        return {}
    emails = person.get("emails") or person.get("email") or []
    if isinstance(emails, list):
        email = (emails[0] or {}).get("value") if emails and isinstance(emails[0], dict) else (emails[0] if emails else "")
    else:
        email = emails
    phones = person.get("phones") or person.get("phone") or []
    if isinstance(phones, list):
        phone = (phones[0] or {}).get("value") if phones and isinstance(phones[0], dict) else (phones[0] if phones else "")
    else:
        phone = phones
    fn, ln = _split_name(person.get("name") or "")
    postal = ""
    addr = person.get("postal_address") or {}
    if isinstance(addr, dict):
        postal = addr.get("postal_code") or ""
    return {
        "email": _norm(email).lower(),
        "phone": _phone_e164(_norm(phone)),
        "first": fn, "last": ln,
        "zip": _norm(postal),
        "country": COUNTRY_DEFAULT,
    }


def _ltv_for(deal: dict) -> float:
    raw = deal.get(DEAL_LTV_KEY)
    try:
        v = float(raw) if raw not in (None, "", 0, "0") else 0.0
        if v > 0:
            return v
    except Exception:
        pass
    score_raw = deal.get(DEAL_SCORE_FIELD_ID)
    try:
        score = int(float(score_raw)) if score_raw not in (None, "") else None
    except Exception:
        score = None
    if score is None:
        return 0.0
    data = compute_ltv(score)
    return float((data or {}).get("ltv") or 0.0)


def fetch_won_deals(limit_total: int | None = None) -> list[dict]:
    out, start, batch = [], 0, 500
    while True:
        params = {"start": start, "limit": batch, "status": "won", "sort": "won_time DESC"}
        resp = _request("/deals", params=params)
        data = resp.get("data") or []
        out.extend(data)
        more = ((resp.get("additional_data") or {}).get("pagination") or {}).get("more_items_in_collection")
        print(f"  fetched={len(out)} more={bool(more)}", flush=True)
        if not data or not more:
            break
        if limit_total and len(out) >= limit_total:
            return out[:limit_total]
        start += batch
        time.sleep(0.2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Máx deals (debug)")
    ap.add_argument("--out", default=None, help="Caminho CSV de saída")
    args = ap.parse_args()

    if not os.environ.get("PIPEDRIVE_API_KEY"):
        print("ERR: defina PIPEDRIVE_API_KEY", file=sys.stderr)
        sys.exit(1)

    print("→ buscando deals WON…", flush=True)
    deals = fetch_won_deals(args.limit)
    print(f"  total WON: {len(deals)}", flush=True)

    by_person: dict[int, dict] = {}
    no_person = 0
    for i, d in enumerate(deals, 1):
        if i % 100 == 0:
            print(f"  processando {i}/{len(deals)}…", flush=True)
        pid_ref = d.get("person_id") or {}
        pid = pid_ref.get("value") if isinstance(pid_ref, dict) else pid_ref
        if not pid:
            no_person += 1
            continue
        ltv = _ltv_for(d)
        if pid in by_person:
            by_person[pid]["ltv"] += ltv
            by_person[pid]["deals"] += 1
            continue
        try:
            person = get_person(pid)
        except Exception as e:
            print(f"  WARN person {pid}: {e}", flush=True)
            person = None
        info = _extract_person(person or {})
        if not info.get("email") and not info.get("phone"):
            continue
        info["ltv"] = ltv
        info["deals"] = 1
        by_person[pid] = info

    out_path = Path(args.out or f"tmp/customer_match_won_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Email", "First Name", "Last Name", "Country", "Zip", "Phone", "LTV"])
        for p in by_person.values():
            w.writerow([p.get("email",""), p.get("first",""), p.get("last",""),
                        p.get("country",""), p.get("zip",""), p.get("phone",""),
                        f"{p['ltv']:.2f}"])

    print(f"\n✅ {len(by_person)} clientes únicos exportados → {out_path}")
    print(f"   (deals sem person: {no_person} | LTV total: R$ {sum(p['ltv'] for p in by_person.values()):,.2f})")


if __name__ == "__main__":
    main()
