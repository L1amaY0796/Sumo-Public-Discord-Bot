import asyncio
import time
from typing import Any, Optional
import aiohttp
BASE_URL = 'https://www.sumo-api.com/api'
CACHE_TTL_SEARCH = 600
CACHE_TTL_RIKISHI_DETAIL = 300
CACHE_TTL_STATS = 180
CACHE_TTL_MATCHES = 120
CACHE_TTL_H2H = 180
CACHE_TTL_BASHO = 300
CACHE_TTL_BANZUKE = 120

class SumoAPIError(Exception):
    pass

class _CacheEntry:
    __slots__ = ('value', 'expires_at')

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl

    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at

class SumoAPI:

    def __init__(self, session: aiohttp.ClientSession, max_concurrent_requests: int=5, default_ttl: float=300.0):
        self._session = session
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._default_ttl = default_ttl
        self._cache: dict[str, _CacheEntry] = {}
        self._inflight: dict[str, 'asyncio.Future[Any]'] = {}

    @staticmethod
    def _cache_key(path: str, params: Optional[dict]) -> str:
        if not params:
            return path
        items = sorted(((str(k), str(v)) for k, v in params.items()))
        return path + '?' + '&'.join((f'{k}={v}' for k, v in items))

    def cache_stats(self) -> dict:
        now = time.monotonic()
        live = sum((1 for e in self._cache.values() if e.expires_at > now))
        return {'total_entries': len(self._cache), 'live_entries': live, 'inflight': len(self._inflight)}

    def clear_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count

    async def _get(self, path: str, params: Optional[dict]=None, ttl: Optional[float]=None) -> Any:
        key = self._cache_key(path, params)
        ttl = self._default_ttl if ttl is None else ttl
        entry = self._cache.get(key)
        if entry is not None and (not entry.is_expired()):
            return entry.value
        existing = self._inflight.get(key)
        if existing is not None:
            return await existing
        future: 'asyncio.Future[Any]' = asyncio.get_event_loop().create_future()
        self._inflight[key] = future
        try:
            result = await self._fetch(path, params)
            self._cache[key] = _CacheEntry(result, ttl)
            future.set_result(result)
            return result
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            self._inflight.pop(key, None)

    async def _fetch(self, path: str, params: Optional[dict]) -> Any:
        url = f'{BASE_URL}{path}'
        async with self._semaphore:
            try:
                async with self._session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        raise SumoAPIError(f'API 回傳狀態碼 {resp.status}：{url}')
                    try:
                        return await resp.json(content_type=None)
                    except Exception as e:
                        raw = await resp.text()
                        raise SumoAPIError(f'回應內容不是有效的 JSON：{url}\n前 300 字元內容：{raw[:300]!r}') from e
            except aiohttp.ClientError as e:
                raise SumoAPIError(f'連線 sumo-api.com 失敗：{e}') from e

    async def search_rikishis(self, shikona_en: Optional[str]=None, heya: Optional[str]=None, intai: Optional[bool]=None, limit: int=50, skip: int=0) -> list:
        params: dict = {'limit': limit, 'skip': skip}
        if shikona_en:
            params['shikonaEn'] = shikona_en
        if heya:
            params['heya'] = heya
        if intai:
            params['intai'] = 'true'
        data = await self._get('/rikishis', params, ttl=CACHE_TTL_SEARCH)
        if isinstance(data, dict):
            return data.get('records', []) or []
        return data or []

    async def get_rikishi(self, rikishi_id: int) -> dict:
        return await self._get(f'/rikishi/{rikishi_id}', {'measurements': 'true', 'ranks': 'true', 'shikonas': 'true'}, ttl=CACHE_TTL_RIKISHI_DETAIL)

    async def get_rikishi_stats(self, rikishi_id: int) -> dict:
        return await self._get(f'/rikishi/{rikishi_id}/stats', ttl=CACHE_TTL_STATS)

    async def get_rikishi_matches(self, rikishi_id: int, basho_id: Optional[str]=None) -> list:
        params = {'bashoId': basho_id} if basho_id else None
        data = await self._get(f'/rikishi/{rikishi_id}/matches', params, ttl=CACHE_TTL_MATCHES)
        if isinstance(data, dict):
            return data.get('records', []) or data.get('matches', []) or []
        return data or []

    async def get_head_to_head(self, rikishi_id: int, opponent_id: int) -> list:
        data = await self._get(f'/rikishi/{rikishi_id}/matches/{opponent_id}', ttl=CACHE_TTL_H2H)
        if isinstance(data, dict):
            return data.get('records', []) or data.get('matches', []) or []
        return data or []

    async def get_basho(self, basho_id: str) -> dict:
        return await self._get(f'/basho/{basho_id}', ttl=CACHE_TTL_BASHO)

    async def get_banzuke(self, basho_id: str, division: str='Makuuchi') -> dict:
        return await self._get(f'/basho/{basho_id}/banzuke/{division}', ttl=CACHE_TTL_BANZUKE)
