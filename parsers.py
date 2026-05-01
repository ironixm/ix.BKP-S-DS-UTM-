# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Parsers – V1.0.0                               │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-03 - 15:41         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ parsers.py                                     │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

# parsers.py
def _clean(value):
    if not value:
        return None
    return value.rstrip("-").strip()


def parse_meta_campaign(raw):
    if not raw or "ix." not in raw:
        return {}

    parts = [p for p in raw.split("ix.") if p.strip()]
    parts = ["ix." + p for p in parts]

    if len(parts) < 2:
        return {}

    campanha = _clean(parts[0])
    anuncio = _clean(parts[-1])

    conjunto_parts = parts[1:-1]
    conjunto = _clean(" | ".join(conjunto_parts)) if conjunto_parts else None
    publico = _clean(conjunto_parts[1]) if len(conjunto_parts) >= 2 else None

    return {
        "campanha_isolada": campanha,
        "conjunto_isolado": conjunto,
        "publico_isolado": publico,
        "anuncio_isolado": anuncio,
    }

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
