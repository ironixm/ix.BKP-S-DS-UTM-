# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Map Fields – V1.0.0                            │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-03-11 - 17:34         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ scripts/map_fields.py                          │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.0 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from pd_api import _request
from dealscore.deal_score_rules import DEAL_SCORE_FIELD_ID
from mappings import DEAL_CANAL_KEY, DEAL_FONTE_KEY, DEAL_CAMPANHA_KEY, DEAL_CONTEUDO_KEY

r = _request('/deals', params={'start': 0, 'limit': 1, 'status': 'all_not_deleted', 'sort': 'id DESC'})
d = r['data'][0]

p = d.get("person_id")
pid = p.get("value") if isinstance(p, dict) else p
org = d.get("org_id")
orgname = org.get("name") if isinstance(org, dict) else org

print("id:", d.get("id"))
print("person_id:", pid)
print("add_time:", d.get("add_time"))
print("label:", d.get("label"))
print("org_name:", orgname)
print("stage_id:", d.get("stage_id"))
print("status:", d.get("status"))
print("canal:", DEAL_CANAL_KEY, "=", d.get(DEAL_CANAL_KEY))
print("fonte:", DEAL_FONTE_KEY, "=", d.get(DEAL_FONTE_KEY))
print("campanha:", DEAL_CAMPANHA_KEY, "=", d.get(DEAL_CAMPANHA_KEY))
print("conteudo:", DEAL_CONTEUDO_KEY, "=", d.get(DEAL_CONTEUDO_KEY))
print("dealscore:", DEAL_SCORE_FIELD_ID, "=", d.get(DEAL_SCORE_FIELD_ID))

r3 = _request('/dealFields')
for f in (r3.get('data') or []):
    if f.get('key') == 'label':
        for o in (f.get('options') or []):
            print("label_opt:", o.get('id'), "=", o.get('label'))
        break

for f in (r3.get('data') or []):
    name = (f.get('name') or '').lower()
    if 'fit' in name:
        print("fit_field:", f.get('key'), "name=", f.get('name'), "val=", d.get(f.get('key')))

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
