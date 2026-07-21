import asyncio
import json
import sys
import aiohttp
from sumo_api import SumoAPI
from utils import current_basho_id
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def main():
    query = sys.argv[1] if len(sys.argv) > 1 else 'Onosato'
    async with aiohttp.ClientSession() as session:
        api = SumoAPI(session)
        print(f'\n=== 1) 搜尋力士：shikonaEn={query} ===')
        candidates = await api.search_rikishis(shikona_en=query, limit=5)
        print(json.dumps(candidates, indent=2, ensure_ascii=False))
        if not candidates:
            print('找不到候選力士，換個羅馬拼音試試，例如 Hoshoryu / Kirishima')
            return
        rikishi_id = candidates[0]['id']
        print(f'\n=== 2) 力士詳細資料：/rikishi/{rikishi_id} ===')
        detail = await api.get_rikishi(rikishi_id)
        print(json.dumps(detail, indent=2, ensure_ascii=False))
        print(f'\n=== 3) 力士生涯統計：/rikishi/{rikishi_id}/stats ===')
        stats = await api.get_rikishi_stats(rikishi_id)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        basho_id = current_basho_id()
        print(f'\n=== 4) 該力士本場所戰績：/rikishi/{rikishi_id}/matches?bashoId={basho_id} ===')
        matches = await api.get_rikishi_matches(rikishi_id, basho_id=basho_id)
        print(json.dumps(matches, indent=2, ensure_ascii=False))
        print(f'\n=== 5) 本場所結果：/basho/{basho_id} ===')
        try:
            basho = await api.get_basho(basho_id)
            print(json.dumps(basho, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f'（查詢失敗，可能該場所還沒開始或資料庫尚未收錄）：{e}')
        print('\n=== 6) 已結束場所結果（測試用）：/basho/202605 ===')
        try:
            finished_basho = await api.get_basho('202605')
            print(json.dumps(finished_basho, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f'（查詢失敗）：{e}')
        print('\n=== 7) 頭對頭對戰紀錄（測試用）：/rikishi/8850/matches/19 ===')
        try:
            h2h = await api.get_head_to_head(8850, 19)
            print(json.dumps(h2h, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f'（查詢失敗）：{e}')
        print(f'\n=== 8) 幕內番付表（測試用）：/basho/{basho_id}/banzuke/Makuuchi ===')
        try:
            banzuke = await api.get_banzuke(basho_id, 'Makuuchi')
            if isinstance(banzuke, dict):
                print('最外層 keys：', list(banzuke.keys()))
                for k, v in banzuke.items():
                    if isinstance(v, list):
                        print(f'\n--- 欄位「{k}」是清單，共 {len(v)} 筆，前 3 筆內容 ---')
                        print(json.dumps(v[:3], indent=2, ensure_ascii=False))
            elif isinstance(banzuke, list):
                print(f'最外層是清單，共 {len(banzuke)} 筆，前 3 筆內容：')
                print(json.dumps(banzuke[:3], indent=2, ensure_ascii=False))
            else:
                print(json.dumps(banzuke, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f'（查詢失敗）：{e}')
if __name__ == '__main__':
    asyncio.run(main())
