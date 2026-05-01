#!/usr/bin/env python3
"""Exporta top N leads (deals OPEN) com DealScore mais alto p/ Customer Match GAds.

Estratégia:
  1. Pagina /deals?status=open (busca todos)
  2. Lê DealScore do campo custom (sem recomputar)
  3. Ordena por score DESC, agrupa por person_id (mantém maior score)
  4. Pega top N pessoas únicas
  5. Busca person + monta CSV (Email, Name, Phone, LTV)

Uso:
  PIPEDRIVE_API_KEY=xxx python3 scripts/export_customer_match_leads.py [--top 5000]
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
from scripts.export_customer_match import (  # type: ignore
    _extract_person, _ltv_for, DEAL_SCORE_FIELD_ID,
)


def fetch_open_deals() -> list[dict]:
    out, start, batch = [], 0, 500
    while True:
        resp = _request("/deals", params={"start": start, "limit": batch, "status": "open"})
        data = resp.get("data") or []
        out.extend(data)
        more = ((resp.get("additional_data") or {}).get("pagination") or {}).get("more_items_in_collection")
        print(f"  fetched={len(out)} more={bool(more)}", flush=True)
        if not data or not more:
            return out
        start += batch
        time.sleep(0.2)


def _score(deal: dict) -> int:
    raw = deal.get(DEAL_SCORE_FIELD_ID)
    try:
        return int(float(raw)) if raw not in (None, "") else -999
    except Exception:
        return -999


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5000)
    ap.add_argument("--min-score", type=int, default=None,
                    help="Score mínimo p/ incluir (default: sem filtro)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if not os.environ.get("PIPEDRIVE_API_KEY"):
        sys.exit("PIPEDRIVE_API_KEY não setado")

    print("→ buscando deals OPEN…", flush=True)
    deals = fetch_open_deals()
    print(f"  total OPEN: {len(deals)}", flush=True)

    # Ordena por score DESC e dedupe por person (mantém maior score)
    deals_sorted = sorted(deals, key=_score, reverse=True)
    by_person: dict[int, dict] = {}
    for d in deals_sorted:
        sc = _score(d)
        if args.min_score is not None and sc < args.min_score:
            break
        pid_ref = d.get("person_id") or {}
        pid = pid_ref.get("value") if isinstance(pid_ref, dict) else pid_ref
        if not pid or pid in by_person:
            continue
        by_person[pid] = {"deal_id": d["id"], "score": sc, "deal": d}
        if len(by_person) >= args.top:
            break

    print(f"  {len(by_person)} pessoas únicas a buscar", flush=True)
    if by_person:
        scores = [v["score"] for v in by_person.values()]
        print(f"  score: max={scores[0]} min={scores[-1]} median={scores[len(scores)//2]}",
              flush=True)

    rows = []
    no_contact = 0
    for i, (pid, meta) in enumerate(by_person.items(), 1):
        if i % 200 == 0:
            print(f"  processando {i}/{len(by_person)}…", flush=True)
        try:
            person = get_person(pid)
        except Exception as e:
            print(f"   WARN person {pid}: {e}", flush=True)
            continue
        info = _extract_person(person or {})
        if not info.get("email") and not info.get("phone"):
            no_contact += 1
            continue
        info["ltv"] = _ltv_for(meta["deal"])
        info["score"] = meta["score"]
        rows.append(info)

    out_path = Path(args.out or
                    f"tmp/customer_match_leads_top{args.top}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Email", "First Name", "Last Name", "Country", "Zip", "Phone", "LTV", "DealScore"])
        for p in rows:
            w.writerow([p.get("email",""), p.get("first",""), p.get("last",""),
                        p.get("country",""), p.get("zip",""), p.get("phone",""),
                        f"{p['ltv']:.2f}", p["score"]])

    total_ltv = sum(p["ltv"] for p in rows)
    print(f"\n✅ {len(rows)} leads exportados → {out_path}")
    print(f"   (sem contato: {no_contact} | LTV total estimado: R$ {total_ltv:,.2f})")


if __name__ == "__main__":
    main()
