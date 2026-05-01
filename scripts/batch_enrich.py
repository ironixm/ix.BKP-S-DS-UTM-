# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Batch Enrich – V1.0.0                          │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-16 - 07:45         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/batch_enrich.py                        │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""Batch processor para enriquecer deals com DealScore, Emoji, Rich Notes."""
import os
import sys
import time

# Ajustar path para importar da raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carregar env
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta

from pd_api import (
    get_deal, get_deals_by_filter, get_person, _request,
    update_deal, update_person, get_deal_notes, add_note, update_note,
)
from dealscore.deal_score import compute_deal_score, build_dealscore_payload, FIELD_IDS
from notes_builder import (
    build_auto_section, compose_full_note, extract_manual_section,
    extract_previous_entries, generate_alerts, _is_auto_note,
)
from main import apply_emoji_prefix, score_to_emoji
from ltv import build_ltv_payload
from mappings import *
from parsers import parse_meta_campaign


def retry(fn, *args, retries=2, delay=3, **kwargs):
    for attempt in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(delay)


def process_one(deal_id, i, total, deal=None, person_cache=None):
    """
    Processa um deal. Se `deal` for passado (objeto completo), evita GET /deals/:id.
    `person_cache` é um dict {person_id: person_obj} compartilhado entre deals.
    Retorna dict com tokens_saved para ajuste de budget.
    """
    if person_cache is None:
        person_cache = {}

    tokens_saved = 0

    if deal is None:
        deal = retry(get_deal, deal_id)
    else:
        tokens_saved += 10  # GET /deals/:id evitado

    if not deal:
        return None

    person_ref = deal.get("person_id") or {}
    person_id = person_ref.get("value") if isinstance(person_ref, dict) else person_ref
    if not person_id:
        return None

    # --- Acumula todas as atualizações do deal em um único payload ---
    deal_updates = {}
    person_updates = {}

    # --- UTM sync ---
    fonte = deal.get(DEAL_FONTE_KEY)
    canal = deal.get(DEAL_CANAL_KEY)
    campanha = deal.get(DEAL_CAMPANHA_KEY)
    if fonte: person_updates[PERSON_FONTE_KEY] = fonte
    if canal: person_updates[PERSON_CANAL_KEY] = canal
    if campanha: person_updates[PERSON_CAMPANHA_KEY] = campanha

    derivados = parse_meta_campaign(campanha)
    for key, df, pf in [
        ("campanha_isolada", DEAL_CAMPANHA_ISOLADA, PERSON_CAMPANHA_ISOLADA),
        ("conjunto_isolado", DEAL_CONJUNTO_ISOLADO, PERSON_CONJUNTO_ISOLADO),
        ("publico_isolado", DEAL_PUBLICO_ISOLADO, PERSON_PUBLICO_ISOLADO),
        ("anuncio_isolado", DEAL_ANUNCIO_ISOLADO, PERSON_ANUNCIO_ISOLADO),
    ]:
        v = derivados.get(key)
        if v:
            if not deal.get(df):
                deal_updates[df] = v
            person_updates[pf] = v

    anuncio = derivados.get("anuncio_isolado")
    if anuncio and not deal.get(DEAL_CONTEUDO_KEY):
        deal_updates[DEAL_CONTEUDO_KEY] = anuncio
        person_updates[PERSON_CONTEUDO_KEY] = anuncio

    if person_updates:
        retry(update_person, person_id, person_updates)

    # --- DealScore (com cache de person) ---
    if person_id in person_cache:
        person_full = person_cache[person_id]
        tokens_saved += 10  # GET /persons/:id evitado (cache hit)
    else:
        person_full = retry(get_person, person_id)
        person_cache[person_id] = person_full

    score = compute_deal_score(deal, person_full, FIELD_IDS)
    deal_updates.update(build_dealscore_payload(score.total))

    # --- Emoji prefix ---
    old_t = deal.get("title") or ""
    new_t = apply_emoji_prefix(old_t, score.total)
    if new_t != old_t:
        deal_updates["title"] = new_t

    # --- LTV / Tenure / ConversionValue ---
    try:
        ltv_payload = build_ltv_payload(deal, score.total)
        if ltv_payload:
            deal_updates.update(ltv_payload)
    except Exception:
        pass

    # --- Single consolidated deal update (saves ~30 tokens vs 4 separate PUTs) ---
    if deal_updates:
        retry(update_deal, deal_id, deal_updates)

    # --- Rich Notes ---
    try:
        notes = retry(get_deal_notes, deal_id)
        auto_notes = [n for n in notes if _is_auto_note(n.get("content") or "")]
        if len(auto_notes) > 1:
            for n in auto_notes[1:]:
                try:
                    retry(_request, f"/notes/{n['id']}", method="DELETE")
                except Exception:
                    pass
        ex_note = auto_notes[0] if auto_notes else None
        ex_html = (ex_note or {}).get("content", "")
        manual = extract_manual_section(ex_html)
        prev = extract_previous_entries(ex_html)
        alertas = generate_alerts(score.total, score.parts, deal)
        auto = build_auto_section(
            score=score.total, parts=score.parts,
            fonte=fonte, canal=canal, campanha=campanha,
            anuncio=deal.get(DEAL_ANUNCIO_ISOLADO),
            alertas=alertas, previous_entries=prev,
            is_initial=(ex_note is None),
        )
        html = compose_full_note(manual, auto)
        if ex_note:
            retry(update_note, ex_note["id"], html)
        else:
            retry(add_note, deal_id, html)
        note_status = "ok"
    except Exception as e:
        note_status = f"err:{e}"

    emoji = score_to_emoji(score.total)
    return {
        "title": new_t, "score": score.total, "emoji": emoji,
        "note": note_status, "person_id": person_id,
        "tokens_saved": tokens_saved,
    }


def fetch_deals_last_year():
    """Busca todos os deals open + won criados nos últimos 12 meses.
    Retorna lista de objetos completos ordenados do mais recente ao mais antigo.
    """
    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    all_deals = []

    for status in ("open", "won"):
        start = 0
        for _ in range(80):  # max 80 pages × 500 = 40k
            j = _request("/deals", params={
                "status": status, "start": start, "limit": 500,
            })
            data = j.get("data") or []
            for d in data:
                ref_date = (d.get("add_time") or "")[:10]
                if ref_date >= cutoff:
                    all_deals.append(d)
            pag = j.get("additional_data", {}).get("pagination", {})
            if not pag.get("more_items_in_collection"):
                break
            start = pag.get("next_start", start + 500)
            time.sleep(0.15)
        print(f"  {status}: {len(all_deals)} deals coletados até aqui")

    # Mais recentes primeiro → prioriza pipeline ativo
    all_deals.sort(key=lambda d: d.get("add_time") or "", reverse=True)
    return all_deals


# Estimativa de tokens por deal (Pipedrive token-based rate limit)
# Com cache de deals + persons:
#   PUT person(10) + PUT deal consolidado(10) + GET notes(7) + PUT/POST note(7) = ~34 tokens/deal
# Sem cache (fallback individual): ~54 tokens/deal
TOKENS_PER_DEAL = 34
# Budget Lite 1 seat = 30.000 tokens/dia. Reserva 10% de margem.
DAILY_TOKEN_BUDGET = int(os.environ.get("PD_DAILY_TOKEN_BUDGET", 27000))

PROGRESS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".batch_progress.txt"
)


def save_progress(deal_ids, index):
    """Salva progresso para permitir retomada."""
    with open(PROGRESS_FILE, "w") as f:
        f.write(f"{index}\n")
        f.write("\n".join(str(d) for d in deal_ids))


def load_progress():
    """Carrega progresso anterior. Retorna (deal_ids, start_index) ou None."""
    if not os.path.exists(PROGRESS_FILE):
        return None
    with open(PROGRESS_FILE) as f:
        lines = f.read().strip().split("\n")
    if len(lines) < 2:
        return None
    start_index = int(lines[0])
    deal_ids = [int(x) for x in lines[1:] if x.strip()]
    return deal_ids, start_index


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Person cache compartilhado entre todos os deals da sessão
    _person_cache = {}
    deals_map = {}  # {deal_id: deal_obj} — evita GET /deals/:id individual

    resumed = False
    if mode == "all" and os.path.exists(PROGRESS_FILE):
        progress = load_progress()
        if progress:
            deal_ids, start_index = progress
            total = len(deal_ids)
            print(f"=== BATCH ENRICH: retomando do deal {start_index+1}/{total} ===")
            # Re-fetch objetos completos para rebuild do cache (custo: ~5 páginas ≈ 50 tokens)
            print("Re-fetching objetos completos para cache de tokens...")
            all_deals = fetch_deals_last_year()
            deals_map = {d["id"]: d for d in all_deals}
            resumed = True

    if not resumed:
        start_index = 0
        if mode == "all":
            print("=== BATCH ENRICH: todos os deals do último ano ===")
            print("Coletando deals (mais recentes primeiro)...")
            all_deals = fetch_deals_last_year()
            deal_ids = [d["id"] for d in all_deals]
            deals_map = {d["id"]: d for d in all_deals}
        else:
            limit = int(mode)
            filter_id = 9870
            print(f"=== BATCH ENRICH: {limit} deals do filtro {filter_id} ===")
            resp = get_deals_by_filter(filter_id, start=0, limit=limit)
            deal_ids = [d["id"] for d in resp["data"] if d.get("id")]

    total = len(deal_ids)
    cache_pct = int(len(deals_map) / total * 100) if total else 0
    print(f"\nTotal a processar: {total} deals (a partir do #{start_index+1})")
    print(f"Cache de deals: {len(deals_map)} objetos ({cache_pct}%) → ~{TOKENS_PER_DEAL} tokens/deal estimado")
    tokens_estimate = (total - start_index) * TOKENS_PER_DEAL
    print(f"Tokens estimados: ~{tokens_estimate:,} (budget diário: {DAILY_TOKEN_BUDGET:,})")
    if tokens_estimate > DAILY_TOKEN_BUDGET:
        batch_today = DAILY_TOKEN_BUDGET // TOKENS_PER_DEAL
        print(f"⚠️  Vai processar ~{batch_today} deals hoje e salvar progresso para continuar amanhã.")
    print()

    ok = erros = skip = 0
    tokens_used = 0
    t0 = time.time()

    for i in range(start_index, total):
        deal_id = deal_ids[i]

        # Verifica se ultrapassou o budget diário estimado
        if tokens_used >= DAILY_TOKEN_BUDGET:
            save_progress(deal_ids, i)
            print(f"\n⚠️  Budget diário estimado atingido (~{tokens_used:,} tokens).")
            print(f"  Progresso salvo em {i}/{total}. Rode novamente amanhã para continuar.")
            break

        try:
            result = process_one(deal_id, i, total,
                                 deal=deals_map.get(deal_id),
                                 person_cache=_person_cache)
            if result is None:
                skip += 1
                tokens_used += 4  # GET deal + partial (sem cache)
                if (i + 1) % 50 == 0:
                    print(f"  [{i+1:4d}/{total}] — Deal {deal_id}: skip")
            else:
                ok += 1
                saved = result.get("tokens_saved", 0)
                tokens_used += max(TOKENS_PER_DEAL - saved, 10)
                t = result["title"][:44]
                s = result["score"]
                n = result["note"]
                print(f"  [{i+1:4d}/{total}] {t:44s} score={s:4d}  note={n}")
        except Exception as ex:
            erros += 1
            tokens_used += 10  # partial
            msg = str(ex)
            print(f"  [{i+1:4d}/{total}] ❌ Deal {deal_id}: {msg}")
            if "Daily limit" in msg or "429" in msg:
                save_progress(deal_ids, i)
                print(f"\n🛑 Rate limit diário atingido. Progresso salvo em {i}/{total}.")
                print(f"  Rode novamente amanhã para continuar.")
                break

        # Rate limit: 0.5s entre deals para margem de segurança
        time.sleep(0.5)

        # Progress report a cada 50
        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            rate = ok / (elapsed / 60) if elapsed > 0 else 0
            persons_cached = len(_person_cache)
            print(f"  --- progresso: {i+1}/{total}  ok={ok} skip={skip} err={erros}  "
                  f"~{tokens_used:,} tokens  {rate:.0f} deals/min  persons_cache={persons_cached} ---")

        # Salva progresso a cada 100 deals
        if (i + 1) % 100 == 0:
            save_progress(deal_ids, i + 1)
    else:
        # Loop completou normalmente — remove arquivo de progresso
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  ✅ OK: {ok}  |  ⏭️ Skip: {skip}  |  ❌ Erros: {erros}  |  Total: {total}")
    print(f"  ⏱️ Tempo: {elapsed/60:.1f} min  |  🪙 Tokens est.: ~{tokens_used:,}")
    print(f"  👤 Persons em cache: {len(_person_cache)}")
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
