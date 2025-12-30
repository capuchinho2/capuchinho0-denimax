import os
import json
from pathlib import Path

def get_cache_path(viagem_id):
    cache_dir = Path(__file__).parent.parent.parent / 'cash_plts'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f'{viagem_id}.json'

def salvar_cache_palete(viagem_id, dados):
    path = get_cache_path(viagem_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False)

def ler_cache_palete(viagem_id):
    path = get_cache_path(viagem_id)
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
