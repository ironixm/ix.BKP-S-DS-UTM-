# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Batch Update All Scores – V1.0.0               │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-03-11 - 17:17         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/batch_update_all_scores.py             │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Batch update COMPLETO: DealScore + UTM sync para Person.
Ordem: MAIS NOVOS primeiro (sort=id DESC).
Executa localmente, sem depender do servidor Flask.
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# carrega .env
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from pd_api import _request, get_deal, get_person, update_deal, update_person
from dealscore.deal_score import FIELD_IDS, build_dealscore_payload, compute_deal_score
from parsers import parse_meta_campaign
from mappings import (
    DEAL_CAMPANHA_KEY, DEAL_CAMPANHA_ISOLADA, DEAL_CONJUNTO_ISOLADO,
    DEAL_PUBLICO_ISOLADO, DEAL_ANUNCIO_ISOLADO, DEAL_CONTEUDO_KEY,
    DEAL_CANAL_KEY, DEAL_FONTE_KEY,
    PERSON_CAMPANHA_KEY, PERSON_CAMPANHA_ISOLADA, PERSON_CONJUNTO_ISOLADO,
    PERSON_PUBLICO_ISOLADO, PERSON_ANUNCIO_ISOLADO, PERSON_CONTEUDO_KEY,
    PERSON_CANAL_KEY, PERSON_FONTE_KEY,
)

LIMIT = 100
# Retomada: ~3100 deals já processados (até Deal ~25223). start=2800 para margem.
RESUME_START = int(os.environ.get("BATCH_RESUME_START", "0"))
start = RESUME_START
total_processed = start  # contagem aproximada
total_updated = 0
total_errors = 0
t0 = time.time()

print("=== BATCH COMPLETO — DEALS + PERSON (mais novos primeiro) ===")
print(f"Início: {time.strftime('%H:%M:%S')}")
print()

while True:
    resp = _request("/deals", params={
        "start": start,
        "limit": LIMIT,
        "status": "all_not_deleted",
        "sort": "id DESC",
    })
    deals = resp.get("data") or []
    if not deals:
        break

    for stub in deals:
        deal_id = stub.get("id")
        if not deal_id:
            continue

        try:
            deal = get_deal(deal_id)
            if not deal:
                continue

            person = deal.get("person_id") or {}
            person_id = person.get("value") if isinstance(person, dict) else None
            person_full = get_person(person_id) if person_id else None

            # --- UTM sync para Person ---
            payload_person = {}
            payload_deal_extra = {}

            fonte = deal.get(DEAL_FONTE_KEY)
            canal = deal.get(DEAL_CANAL_KEY)
            campanha = deal.get(DEAL_CAMPANHA_KEY)

            if fonte and person_id:
                payload_person[PERSON_FONTE_KEY] = fonte
            if canal and person_id:
                payload_person[PERSON_CANAL_KEY] = canal
            if campanha and person_id:
                payload_person[PERSON_CAMPANHA_KEY] = campanha

            derivados = parse_meta_campaign(campanha)
            for key, deal_field, person_field in [
                ("campanha_isolada", DEAL_CAMPANHA_ISOLADA, PERSON_CAMPANHA_ISOLADA),
                ("conjunto_isolado", DEAL_CONJUNTO_ISOLADO, PERSON_CONJUNTO_ISOLADO),
                ("publico_isolado", DEAL_PUBLICO_ISOLADO, PERSON_PUBLICO_ISOLADO),
                ("anuncio_isolado", DEAL_ANUNCIO_ISOLADO, PERSON_ANUNCIO_ISOLADO),
            ]:
                value = derivados.get(key)
                if value:
                    if not deal.get(deal_field):
                        payload_deal_extra[deal_field] = value
                    if person_id:
                        payload_person[person_field] = value

            anuncio = derivados.get("anuncio_isolado")
            if anuncio and not deal.get(DEAL_CONTEUDO_KEY):
                payload_deal_extra[DEAL_CONTEUDO_KEY] = anuncio
                if person_id:
                    payload_person[PERSON_CONTEUDO_KEY] = anuncio

            if payload_person and person_id:
                update_person(person_id, payload_person)

            if payload_deal_extra:
                update_deal(deal_id, payload_deal_extra)

            # --- DealScore ---
            score = compute_deal_score(
                deal=deal,
                person=person_full,
                field_ids=FIELD_IDS,
            )
            update_deal(deal_id, build_dealscore_payload(score.total))
            total_updated += 1

            status = deal.get("status", "?")
            title = (deal.get("title") or "?")[:40]
            utm = "UTM" if payload_person else "   "
            print(f"  [{total_processed+1:>4}] Deal {deal_id:>6} | score={score.total:>4} | {utm} | {status:<5} | {title}")

        except Exception as e:
            total_errors += 1
            print(f"  [{total_processed+1:>4}] Deal {deal_id:>6} | ERRO: {e}")

        total_processed += 1

    pagination = resp.get("additional_data", {}).get("pagination", {})
    has_more = pagination.get("more_items_in_collection", False)
    if not has_more:
        break
    start = pagination.get("next_start", start + LIMIT)

elapsed = time.time() - t0
print()
print(f"=== CONCLUÍDO em {elapsed:.0f}s ===")
print(f"  Processados: {total_processed}")
print(f"  Atualizados: {total_updated}")
print(f"  Erros:       {total_errors}")
print(f"  Velocidade:  {total_processed/max(elapsed,1):.1f} deals/s")

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
