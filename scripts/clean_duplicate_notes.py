# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Clean Duplicate Notes – V1.0.0                 │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 16:23         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/clean_duplicate_notes.py               │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Limpa notas automáticas duplicadas do batch, mantendo só a mais recente por deal.

Abordagem eficiente: busca TODAS as notas via /notes (paginado), agrupa por deal,
e deleta duplicatas — muito menos requests que buscar nota-a-nota por deal.

Uso:
  python scripts/clean_duplicate_notes.py 22256     # limpa um deal específico
  python scripts/clean_duplicate_notes.py all        # limpa todos (via paginação de notes)
"""
import os, sys, time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from pd_api import get_deal_notes, _request
from notes_builder import _is_auto_note


def _safe_request(fn, *args, retries=8, **kwargs):
    """Retry com backoff em caso de 429 (rate limit)."""
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                wait = 10 * (attempt + 1)
                print(f"    ⏳ Rate limit, aguardando {wait}s...")
                time.sleep(wait)
            else:
                raise


def delete_note(note_id):
    """Deleta uma nota do Pipedrive (DELETE real)."""
    return _request(f"/notes/{note_id}", method="DELETE")


def fetch_all_notes():
    """Busca TODAS as notas do Pipedrive via paginação. Agrupa por deal_id."""
    notes_by_deal = defaultdict(list)
    start = 0
    page = 0

    while True:
        page += 1
        j = _safe_request(_request, "/notes", params={
            "start": start, "limit": 500, "sort": "add_time DESC",
        })
        data = j.get("data") or []

        for n in data:
            deal_id = n.get("deal_id")
            if deal_id and _is_auto_note(n.get("content") or ""):
                notes_by_deal[deal_id].append(n)

        pag = j.get("additional_data", {}).get("pagination", {})
        print(f"  Página {page}: {len(data)} notas lidas, {len(notes_by_deal)} deals com notas auto")

        if not pag.get("more_items_in_collection"):
            break
        start = pag.get("next_start", start + 500)
        time.sleep(2)  # Rate limit conservador

    return notes_by_deal


def clean_deal_single(deal_id):
    """Limpa duplicatas de UM deal (modo rápido)."""
    notes = _safe_request(get_deal_notes, deal_id)
    auto_notes = [n for n in notes if _is_auto_note(n.get("content") or "")]

    if len(auto_notes) <= 1:
        print(f"  Deal {deal_id}: {len(notes)} notas, {len(auto_notes)} auto — OK")
        return 0

    to_delete = auto_notes[1:]
    print(f"  Deal {deal_id}: {len(auto_notes)} auto → deletando {len(to_delete)} duplicata(s)")

    removed = 0
    for n in to_delete:
        try:
            _safe_request(delete_note, n["id"])
            print(f"    🗑️  Nota {n['id']} deletada")
            removed += 1
            time.sleep(1)
        except Exception as e:
            print(f"    ❌ Erro nota {n['id']}: {e}")
    return removed


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode != "all":
        deal_id = int(mode)
        print(f"=== LIMPEZA DE DUPLICATAS: Deal {deal_id} ===")
        removed = clean_deal_single(deal_id)
        print(f"\n✅ {removed} nota(s) duplicada(s) removida(s)")
        return

    # --- Modo bulk: busca todas as notas de uma vez ---
    print("=== LIMPEZA DE DUPLICATAS (BULK) ===")
    print("Buscando todas as notas do Pipedrive...")
    notes_by_deal = fetch_all_notes()

    # Filtrar deals com mais de 1 nota automática
    dupes = {did: ns for did, ns in notes_by_deal.items() if len(ns) > 1}
    print(f"\n{len(dupes)} deals com notas automáticas duplicadas")

    if not dupes:
        print("✅ Nenhuma duplicata encontrada!")
        return

    total_removed = 0
    for did, auto_notes in dupes.items():
        # auto_notes já vem ordenado por add_time DESC, [0] é o mais recente
        to_delete = auto_notes[1:]
        print(f"\n  Deal {did}: {len(auto_notes)} auto → deletando {len(to_delete)}")

        for n in to_delete:
            try:
                _safe_request(delete_note, n["id"])
                print(f"    🗑️  Nota {n['id']} deletada")
                total_removed += 1
                time.sleep(1)
            except Exception as e:
                print(f"    ❌ Erro nota {n['id']}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Limpeza concluída:")
    print(f"   Deals com duplicatas: {len(dupes)}")
    print(f"   Notas removidas: {total_removed}")
    print(f"{'='*60}")


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
