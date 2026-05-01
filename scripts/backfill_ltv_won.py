#!/usr/bin/env python3
"""Backfill DealScore + LTV nos deals WON antigos sem LTV calculado.

Pipeline por deal:
  1. prefill_dealscore_fields.process_one   (preenche Lead indicado, CRM Pref, etc.)
  2. compute_deal_score(deal+person)        (recalcula score com campos novos)
  3. build_dealscore_payload + LTV/CV       (grava no Pipedrive se faltar)

Skipa deals que JÁ têm LTV > 0 (sinal de manual/preenchido).
Respeita quota Pipedrive (auto-pause em 429).

Uso:
  PIPEDRIVE_API_KEY=xxx python3 scripts/backfill_ltv_won.py [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pd_api import _request, get_deal, get_person, update_deal  # type: ignore
from mappings import DEAL_LTV_KEY, DEAL_CONVERSION_VALUE_KEY  # type: ignore
from ltv import compute_ltv  # type: ignore
from dealscore.deal_score import compute_deal_score, FIELD_IDS  # type: ignore
from dealscore.deal_score_rules import apply_emoji_prefix, DEAL_SCORE_FIELD_ID  # type: ignore
from scripts.prefill_dealscore_fields import process_one as prefill_one  # type: ignore


def fetch_won_deal_ids() -> list[int]:
    out, start, batch = [], 0, 500
    while True:
        resp = _request("/deals", params={"start": start, "limit": batch,
                                          "status": "won", "sort": "won_time DESC"})
        data = resp.get("data") or []
        out.extend(int(d["id"]) for d in data if d.get("id"))
        more = ((resp.get("additional_data") or {}).get("pagination") or {}).get("more_items_in_collection")
        print(f"  fetched={len(out)} more={bool(more)}", flush=True)
        if not data or not more:
            return out
        start += batch
        time.sleep(0.2)


def _has_ltv(deal: dict) -> bool:
    raw = deal.get(DEAL_LTV_KEY)
    try:
        return raw not in (None, "", 0, "0") and float(raw) > 0
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Limite (debug)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--throttle", type=float, default=0.5, help="seg/deal")
    ap.add_argument("--skip-prefill", action="store_true", help="só LTV, sem prefill")
    args = ap.parse_args()

    if not os.environ.get("PIPEDRIVE_API_KEY"):
        sys.exit("PIPEDRIVE_API_KEY não setado")

    print("→ buscando IDs de deals WON…", flush=True)
    ids = fetch_won_deal_ids()
    if args.limit:
        ids = ids[:args.limit]
    print(f"  total: {len(ids)}", flush=True)

    counts = {"already_ltv": 0, "prefill_ok": 0, "score_written": 0,
              "ltv_written": 0, "no_score": 0, "errors": 0}

    for i, did in enumerate(ids, 1):
        if i % 20 == 0:
            print(f"  [{i}/{len(ids)}] {counts}", flush=True)
        try:
            deal = get_deal(did)
            if not deal:
                continue
            if _has_ltv(deal):
                counts["already_ltv"] += 1
                continue

            # 1) Prefill DS input fields
            if not args.skip_prefill and not args.dry_run:
                try:
                    res = prefill_one(deal, dry_run=False, with_headcount=True)
                    if res.get("action") == "updated":
                        counts["prefill_ok"] += 1
                        deal = get_deal(did) or deal  # refetch p/ score
                except Exception as e:
                    print(f"   WARN prefill {did}: {str(e)[:120]}", flush=True)

            # 2) Score
            pid_ref = deal.get("person_id") or {}
            pid = pid_ref.get("value") if isinstance(pid_ref, dict) else pid_ref
            person = get_person(pid) if pid else None
            score = compute_deal_score(deal, person, FIELD_IDS)
            if score is None:
                counts["no_score"] += 1
                continue

            # 3) Build payload: score + LTV/CV
            payload = {DEAL_SCORE_FIELD_ID: score.total}

            # Para WON: tenta tier-table; se score baixo, usa deal.value como fallback
            ltv_data = compute_ltv(score.total) if score.total >= 0 else None
            deal_value = deal.get("value") or 0
            try:
                deal_value = float(deal_value)
            except Exception:
                deal_value = 0.0

            if ltv_data and ltv_data.get("ltv"):
                ltv_val = ltv_data["ltv"]
                cv_val = ltv_data["conversion_value"]
            elif deal_value > 0:
                # Fallback WON: valor fechado * 12 meses como LTV estimado
                ltv_val = deal_value * 12
                cv_val = deal_value
            else:
                # Fallback final WON sem value: ticket médio histórico
                ltv_val = float(os.environ.get("WON_FALLBACK_LTV", 7500))
                cv_val = float(os.environ.get("WON_FALLBACK_CV", 625))

            if ltv_val and not deal.get(DEAL_LTV_KEY):
                payload[DEAL_LTV_KEY] = ltv_val
            if cv_val and not deal.get(DEAL_CONVERSION_VALUE_KEY):
                payload[DEAL_CONVERSION_VALUE_KEY] = cv_val

            old_title = deal.get("title") or ""
            new_title = apply_emoji_prefix(old_title, score.total)
            if new_title != old_title:
                payload["title"] = new_title

            if args.dry_run:
                print(f"   DRY {did}: score={score.total} payload={payload}", flush=True)
            else:
                update_deal(did, payload)
                counts["score_written"] += 1
                if DEAL_LTV_KEY in payload:
                    counts["ltv_written"] += 1

            time.sleep(args.throttle)
        except Exception as e:
            counts["errors"] += 1
            msg = str(e)[:200]
            print(f"   ERR {did}: {msg}", flush=True)
            if "429" in msg or "quota" in msg.lower():
                print("   ⏸  quota — pausando 60s", flush=True)
                time.sleep(60)

    print(f"\n✅ Concluído: {counts}")


if __name__ == "__main__":
    main()
