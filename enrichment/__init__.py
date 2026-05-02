"""ix.BKP/BLZ — Enrichment package.

Port em Python do enrichmentService.js (BKP-Leads-Sync v2).

Pipeline:
    1. CNPJ chain (BrasilAPI → MinhaReceita → ReceitaWS)
    2. Email checks (commercial/disposable)
    3. Company details + logo (NinjaPear — opcional)
    4. WhatsApp Business check
    5. LinkedIn discovery (Google CSE fallback)
    6. Org build + person↔org link

Cada projeto fornece um *adapter* (Agendor ou Pipedrive) que mapeia
campos custom e implementa get/update do CRM.
"""
from .pipeline import enrich_organization, enrich_person  # noqa: F401
