import json
import difflib
from pathlib import Path
from typing import Optional
from sumo_api import SumoAPI
ALIASES_PATH = Path(__file__).parent / 'aliases.json'

def _load_aliases() -> dict:
    if not ALIASES_PATH.exists():
        return {}
    with open(ALIASES_PATH, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    raw.pop('_說明', None)
    normalized = {}
    for k, v in raw.items():
        normalized[k] = v
        normalized[k.lower()] = v
    return normalized
_ALIASES = _load_aliases()

def reload_aliases() -> None:
    global _ALIASES
    _ALIASES = _load_aliases()

def _normalize_romaji(s: str) -> str:
    if s.isascii() and s.isalpha():
        return s.capitalize()
    return s

async def resolve_rikishi(api: SumoAPI, query: str) -> Optional[dict]:
    query = (query or '').strip()
    if not query:
        return None
    search_term = _ALIASES.get(query) or _ALIASES.get(query.lower()) or _normalize_romaji(query)
    candidates = await api.search_rikishis(shikona_en=search_term, intai=False, limit=50)
    if not candidates:
        candidates = await api.search_rikishis(shikona_en=search_term, intai=True, limit=50)
    if not candidates and search_term != query:
        candidates = await api.search_rikishis(shikona_en=query, intai=True, limit=50)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    def score(c: dict) -> float:
        en = c.get('shikonaEn') or ''
        jp = c.get('shikonaJp') or ''
        return max(difflib.SequenceMatcher(None, search_term.lower(), en.lower()).ratio(), difflib.SequenceMatcher(None, query, jp).ratio())
    return max(candidates, key=score)
