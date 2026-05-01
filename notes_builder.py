# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Notes Builder – V1.0.0                         │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-04-15 - 16:23         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ notes_builder.py                               │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

"""
Rich Notes builder para Pipedrive.

Gera HTML com seções manual (preservada) e automática (atualizada a cada sync).
Formato:
  [conteúdo manual digitado pelo usuário]
  <hr>
  <!-- IX_AUTO_START -->
  [seção automática gerada pelo sistema]
  <!-- IX_AUTO_END -->
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from dealscore.deal_score_rules import score_to_emoji

# Marcadores que delimitam a seção automática
# Pipedrive REMOVE comentários HTML, então usamos um padrão visível detectável
AUTO_MARKER = "ix.auto.dealscore"
AUTO_START = f'<div data-ix="{AUTO_MARKER}">'
AUTO_END = "</div>"
DIVIDER = "<hr>"

# Padrão legado (para encontrar notas antigas sem marcador). Match agressivo:
# qualquer nota que mencione "DealScore:" nos primeiros ~200 chars é nossa.
LEGACY_AUTO_PATTERN = re.compile(
    r'^\s*<hr>\s*<(?:div|h3)[^>]*>[\s\S]{0,40}DealScore:',
    re.IGNORECASE,
)
LEGACY_FALLBACK_PATTERN = re.compile(
    r'^[\s\S]{0,120}(?:<h[1-6][^>]*>|<b>|<strong>|🪨|🌱|🌿|🌳|🌟)[\s\S]{0,40}DealScore:',
    re.IGNORECASE,
)

# =====================================================
# UTM → humano
# =====================================================

_UTM_SOURCE_MAP = {
    "google": "Google Ads",
    "facebook": "Meta Ads (Facebook)",
    "fb": "Meta Ads (Facebook)",
    "instagram": "Meta Ads (Instagram)",
    "ig": "Meta Ads (Instagram)",
    "meta": "Meta Ads",
    "linkedin": "LinkedIn Ads",
    "tiktok": "TikTok Ads",
    "youtube": "YouTube",
    "bing": "Bing Ads",
    "email": "E-mail Marketing",
    "organic": "Orgânico",
    "referral": "Indicação",
    "direct": "Direto",
}


def _humanize_source(raw: str | None) -> str:
    if not raw:
        return "Não identificada"
    key = raw.strip().lower()
    return _UTM_SOURCE_MAP.get(key, raw)


# =====================================================
# DealScore timeline entry
# =====================================================

def format_score_entry(score: int, parts: dict[str, int], is_initial: bool = False) -> str:
    """Formata uma entrada de timeline do DealScore."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        # Fallback: UTC-3 manual
        from datetime import timedelta
        now = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")
    label = "Formação inicial" if is_initial else "Atualização"

    # Prioridade: campos do grupo "Deal Score" (prefixo client_*) primeiro,
    # ordenados por |peso| desc. Demais componentes vêm como secundários.
    priority = [(k, v) for k, v in parts.items() if v != 0 and k.startswith("client_")]
    secondary = [(k, v) for k, v in parts.items() if v != 0 and not k.startswith("client_")]
    priority.sort(key=lambda x: abs(x[1]), reverse=True)
    secondary.sort(key=lambda x: abs(x[1]), reverse=True)

    def _fmt(items):
        return ", ".join(f"{k}: {'+' if v > 0 else ''}{v}" for k, v in items)

    pri_str = _fmt(priority) if priority else ""
    sec_str = _fmt(secondary[:5]) if secondary else ""

    if pri_str and sec_str:
        parts_str = f"<b>prioridade:</b> {pri_str} | <i>secundários:</i> {sec_str}"
    elif pri_str:
        parts_str = f"<b>prioridade:</b> {pri_str}"
    elif sec_str:
        parts_str = sec_str
    else:
        parts_str = "sem componentes"

    return (
        f"<b>{label}</b> — {now} — "
        f"Score: <b>{score}</b> ({parts_str})"
    )


# =====================================================
# Seção automática completa
# =====================================================

def build_auto_section(
    score: int,
    parts: dict[str, int],
    fonte: str | None = None,
    canal: str | None = None,
    campanha: str | None = None,
    anuncio: str | None = None,
    alertas: list[str] | None = None,
    previous_entries: list[str] | None = None,
    is_initial: bool = False,
) -> str:
    """Gera o bloco HTML da seção automática."""
    lines: list[str] = []

    # --- Resumo ---
    emoji = score_to_emoji(score)
    lines.append(f"<h3>{emoji} DealScore: {score}</h3>")

    # --- Alertas ---
    if alertas:
        lines.append("<p><b>⚠️ Alertas:</b></p><ul>")
        for a in alertas:
            lines.append(f"<li>{a}</li>")
        lines.append("</ul>")

    # --- Fonte (UTM decodificada) ---
    lines.append("<p><b>📡 Origem:</b></p><ul>")
    lines.append(f"<li>Fonte: {_humanize_source(fonte)}</li>")
    if canal:
        lines.append(f"<li>Canal: {canal}</li>")
    if campanha:
        lines.append(f"<li>Campanha: {campanha}</li>")
    if anuncio:
        lines.append(f"<li>Anúncio: {anuncio}</li>")
    lines.append("</ul>")

    # --- Timeline DealScore ---
    lines.append("<p><b>📊 Histórico DealScore:</b></p><ul>")
    new_entry = format_score_entry(score, parts, is_initial=is_initial)
    lines.append(f"<li>{new_entry}</li>")
    if previous_entries:
        for entry in previous_entries:
            lines.append(f"<li>{entry}</li>")
    lines.append("</ul>")

    return "\n".join(lines)


# =====================================================
# Gerar alertas automáticos
# =====================================================

def generate_alerts(score: int, parts: dict[str, int], deal: dict) -> list[str]:
    """Gera lista de alertas baseados nos componentes do score."""
    alerts = []

    if parts.get("status", 0) < 0:
        alerts.append("Deal marcado como <b>perdido</b>")

    if parts.get("stagnation", 0) <= -20:
        alerts.append("Deal <b>estagnado</b> há muito tempo — considere follow-up ou arquivar")

    if parts.get("email", 0) < 0:
        alerts.append("E-mail inválido ou ausente")

    if parts.get("phone", 0) < 0:
        alerts.append("Telefone inválido ou ausente")

    if parts.get("site", 0) < 0:
        alerts.append("Site não validado")

    if score < 0:
        alerts.append("Score negativo — prioridade muito baixa")

    return alerts


# =====================================================
# Montar / atualizar nota completa
# =====================================================

def _is_auto_note(content: str) -> bool:
    """Detecta se uma nota é automática (novo marcador OU padrão legado)."""
    if not content:
        return False
    if AUTO_MARKER in content:
        return True
    if LEGACY_AUTO_PATTERN.search(content):
        return True
    # Fallback ultra-permissivo: qualquer nota que tenha "DealScore: <número>"
    # nos primeiros 300 chars é considerada automática (legado).
    if LEGACY_FALLBACK_PATTERN.search(content[:300]):
        return True
    return False


def extract_previous_entries(existing_html: str) -> list[str]:
    """Extrai entradas anteriores do timeline a partir de HTML existente."""
    entries = []
    # Tenta novo marcador primeiro, senão usa todo o conteúdo
    match = re.search(
        rf"{re.escape(AUTO_START)}(.*?){re.escape(AUTO_END)}",
        existing_html,
        re.DOTALL,
    )
    auto_block = match.group(1) if match else existing_html

    # Pega os <li> que contêm entradas de timeline
    pattern = re.compile(r"<li>(<b>(?:Formação inicial|Atualização)</b>.*?)</li>", re.DOTALL)
    for m in pattern.finditer(auto_block):
        entries.append(m.group(1))

    return entries


def extract_manual_section(existing_html: str) -> str:
    """Extrai a parte manual (antes do <hr> ou do AUTO_START)."""
    if not existing_html:
        return ""

    # Se tem novo marcador, tudo antes dele é manual
    auto_pos = existing_html.find(AUTO_START)
    if auto_pos >= 0:
        before = existing_html[:auto_pos].strip()
        # Remove trailing <hr> se houver
        if before.endswith(DIVIDER):
            before = before[:-len(DIVIDER)].strip()
        return before

    # Se é nota legada (auto sem marcador), verificar se é puramente automática
    if _is_auto_note(existing_html):
        # Nota legada automática — sem seção manual
        return ""

    # Se tem <hr>, tudo antes é manual
    hr_pos = existing_html.find(DIVIDER)
    if hr_pos >= 0:
        return existing_html[:hr_pos].strip()

    # Sem markers — todo o conteúdo é manual
    return existing_html.strip()


def compose_full_note(manual: str, auto_html: str) -> str:
    """Junta seção manual + divider + seção automática."""
    parts = []
    if manual:
        parts.append(manual)
    parts.append(DIVIDER)
    parts.append(AUTO_START)
    parts.append(auto_html)
    parts.append(AUTO_END)
    return "\n".join(parts)

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
