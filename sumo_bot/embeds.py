import discord
from typing import Optional
from utils import calc_age, basho_display_name, translate_rank, translate_division
BRAND_COLOR = discord.Color.from_rgb(180, 40, 40)

def _display_name(rikishi: dict) -> str:
    en = rikishi.get('shikonaEn') or '?'
    jp = rikishi.get('shikonaJp')
    return f'{jp}（{en}）' if jp else en

def _match_result_for(match: dict, rikishi_id: int) -> tuple[str, Optional[dict]]:
    east_id = match.get('eastId')
    west_id = match.get('westId')
    winner_id = match.get('winnerId')
    if east_id == rikishi_id:
        opponent = {'shikonaEn': match.get('westShikona'), 'id': west_id, 'rank': match.get('westRank')}
    elif west_id == rikishi_id:
        opponent = {'shikonaEn': match.get('eastShikona'), 'id': east_id, 'rank': match.get('eastRank')}
    else:
        opponent = None
    if winner_id is None:
        return ('unknown', opponent)
    return ('win' if winner_id == rikishi_id else 'loss', opponent)

def build_rikishi_embed(rikishi: dict, stats: Optional[dict]) -> discord.Embed:
    name = _display_name(rikishi)
    embed = discord.Embed(title=f'🀄 {name}', color=BRAND_COLOR)
    age = calc_age(rikishi.get('birthDate'))
    current_rank = rikishi.get('currentRank')
    embed.add_field(name='目前番付', value=f'{translate_rank(current_rank)}（{current_rank}）' if current_rank else '不明', inline=True)
    embed.add_field(name='年齡', value=f'{age} 歲' if age is not None else '不明', inline=True)
    embed.add_field(name='所屬部屋', value=rikishi.get('heya') or '不明', inline=True)
    embed.add_field(name='出身地', value=rikishi.get('shusshin') or '不明', inline=True)
    height = rikishi.get('height')
    weight = rikishi.get('weight')
    embed.add_field(name='身體數據', value=f'{height} cm / {weight} kg' if height and weight else '不明', inline=True)
    debut = rikishi.get('debut')
    embed.add_field(name='初土俵', value=basho_display_name(debut) if debut else '不明', inline=True)
    ranks = rikishi.get('rankHistory') or rikishi.get('ranks')
    if ranks:
        recent = ranks[:5] if isinstance(ranks, list) else []
        lines = []
        for r in recent:
            bid = r.get('bashoId', '?')
            rk = r.get('rank') or r.get('rankValue') or '?'
            lines.append(f'{basho_display_name(str(bid))}：{(translate_rank(rk) if isinstance(rk, str) else rk)}（{rk}）')
        if lines:
            embed.add_field(name='近期番付異動', value='\n'.join(lines), inline=False)
    if stats:
        total_wins = stats.get('totalWins')
        total_losses = stats.get('totalLosses')
        total_matches = stats.get('totalMatches')
        record_line = f'{total_wins} 勝 {total_losses} 敗（共 {total_matches} 場）' if total_wins is not None else '資料不明'
        embed.add_field(name='生涯總戰績', value=record_line, inline=False)
        yusho_count = stats.get('yusho')
        if yusho_count:
            yusho_by_div = stats.get('yushoByDivision') or {}
            breakdown = '、'.join((f'{div} {n}次' for div, n in yusho_by_div.items()))
            value = f'共 {yusho_count} 次' + (f'（{breakdown}）' if breakdown else '')
            embed.add_field(name='🏆 優勝次數', value=value, inline=False)
        sansho = stats.get('sansho') or {}
        if sansho:
            sansho_names = {'Gino-sho': '技能賞', 'Kanto-sho': '敢鬥賞', 'Shukun-sho': '殊勳賞'}
            lines = [f'{sansho_names.get(k, k)}：{v} 次' for k, v in sansho.items()]
            embed.add_field(name='🎖️ 三賞', value='\n'.join(lines), inline=False)
    embed.set_footer(text='資料來源：sumo-api.com')
    return embed

def build_record_embed(rikishi: dict, basho_id: str, matches: list) -> discord.Embed:
    name = _display_name(rikishi)
    rikishi_id = rikishi.get('id')
    embed = discord.Embed(title=f'📋 {name} — {basho_display_name(basho_id)} 戰績', color=BRAND_COLOR)
    if not matches:
        embed.description = '目前查不到這個場所的比賽紀錄（可能場所尚未開始，或該力士這場所沒有出場）。'
        return embed
    matches_sorted = sorted(matches, key=lambda m: m.get('day', 0))
    wins = losses = 0
    lines = []
    for m in matches_sorted:
        result, opponent = _match_result_for(m, rikishi_id)
        day = m.get('day', '?')
        opp_name = (opponent or {}).get('shikonaEn') or '?'
        kimarite = m.get('kimarite') or ''
        if result == 'win':
            wins += 1
            mark = '🔵 勝'
        elif result == 'loss':
            losses += 1
            mark = '🔴 敗'
        else:
            mark = '⚪ 未知'
        line = f'第{day}日\u3000{mark}\u3000vs {opp_name}'
        if kimarite:
            line += f'（{kimarite}）'
        lines.append(line)
    embed.description = '\n'.join(lines)
    embed.add_field(name='目前戰績', value=f'{wins} 勝 {losses} 敗', inline=False)
    embed.set_footer(text='資料來源：sumo-api.com（進行中的場所會即時反映目前戰況）')
    return embed

def build_h2h_embed(rikishi_a: dict, rikishi_b: dict, matches: list) -> discord.Embed:
    name_a = _display_name(rikishi_a)
    name_b = _display_name(rikishi_b)
    id_a = rikishi_a.get('id')
    embed = discord.Embed(title=f'⚔️ {name_a}  vs  {name_b}', color=BRAND_COLOR)
    if not matches:
        embed.description = '查不到這兩位力士的對戰紀錄（可能兩人從未在幕內等有紀錄的番付交手過）。'
        return embed
    wins_a = wins_b = 0
    for m in matches:
        winner_id = m.get('winnerId')
        if winner_id == id_a:
            wins_a += 1
        elif winner_id is not None:
            wins_b += 1
    embed.add_field(name='總對戰次數', value=f'{len(matches)} 場', inline=False)
    embed.add_field(name=name_a, value=f'{wins_a} 勝', inline=True)
    embed.add_field(name=name_b, value=f'{wins_b} 勝', inline=True)
    short_a = (rikishi_a.get('shikonaJp') or '').split('\u3000')[0] or rikishi_a.get('shikonaEn') or '?'
    short_b = (rikishi_b.get('shikonaJp') or '').split('\u3000')[0] or rikishi_b.get('shikonaEn') or '?'
    matches_sorted = sorted(matches, key=lambda m: (m.get('bashoId', ''), m.get('day', 0)), reverse=True)
    lines = []
    for m in matches_sorted[:10]:
        bid = str(m.get('bashoId', '?'))
        day = m.get('day', '?')
        kimarite = m.get('kimarite') or '?'
        winner_id = m.get('winnerId')
        winner_name = short_a if winner_id == id_a else short_b if winner_id else '?'
        lines.append(f'{bid} Day{day} {winner_name}勝（{kimarite}）')
    if lines:
        embed.add_field(name='最近對戰紀錄', value='\n'.join(lines), inline=False)
    embed.set_footer(text='資料來源：sumo-api.com')
    return embed

def build_basho_embed(basho_id: str, basho_data: dict, banzuke: Optional[dict]=None) -> discord.Embed:
    embed = discord.Embed(title=f'🏆 {basho_display_name(basho_id)} 結果', color=BRAND_COLOR)
    start = basho_data.get('startDate')
    end = basho_data.get('endDate')
    if start or end:
        start_short = (start or '?')[:10]
        end_short = (end or '?')[:10]
        embed.add_field(name='賽程', value=f'{start_short} ～ {end_short}', inline=False)
    yusho = basho_data.get('yusho')
    if yusho:
        lines = []
        for y in yusho:
            division = translate_division(y.get('type'))
            name_jp = y.get('shikonaJp')
            name_en = y.get('shikonaEn') or '?'
            display = f'{name_jp}（{name_en}）' if name_jp else name_en
            lines.append(f'{division}：{display}')
        embed.add_field(name='🏅 各級優勝', value='\n'.join(lines), inline=False)
        special_prizes = basho_data.get('specialPrizes')
        if special_prizes:
            sansho_names = {'Gino-sho': '技能賞', 'Kanto-sho': '敢鬥賞', 'Shukun-sho': '殊勳賞'}
            lines = []
            for s in special_prizes:
                prize = sansho_names.get(s.get('type'), s.get('type') or '?')
                name_jp = s.get('shikonaJp')
                name_en = s.get('shikonaEn') or '?'
                display = f'{name_jp}（{name_en}）' if name_jp else name_en
                lines.append(f'{prize}：{display}')
            embed.add_field(name='🎖️ 三賞', value='\n'.join(lines), inline=False)
    else:
        embed.add_field(name='📢 場所狀態', value='進行中', inline=False)
        if banzuke:
            entries = (banzuke.get('east') or []) + (banzuke.get('west') or [])
            entries_sorted = sorted(entries, key=lambda e: (-(e.get('wins') or 0), e.get('losses') or 0, e.get('rankValue') or 999))
            MAX_DISPLAY = 10
            display_entries = list(entries_sorted[:5])
            if len(entries_sorted) > 5:
                cutoff = (entries_sorted[4].get('wins') or 0, entries_sorted[4].get('losses') or 0)
                idx = 5
                while idx < len(entries_sorted) and len(display_entries) < MAX_DISPLAY:
                    e = entries_sorted[idx]
                    score = (e.get('wins') or 0, e.get('losses') or 0)
                    if score != cutoff:
                        break
                    display_entries.append(e)
                    idx += 1
            lines = []
            rank = 0
            prev_score = None
            for i, e in enumerate(display_entries):
                score = (e.get('wins') or 0, e.get('losses') or 0)
                if score != prev_score:
                    rank = i + 1
                    prev_score = score
                name_jp = e.get('shikonaJp')
                name_en = e.get('shikonaEn') or '?'
                display = f'{name_jp}（{name_en}）' if name_jp else name_en
                wins, losses = score
                rank_str = e.get('rank') or ''
                lines.append(f'{rank}. {display} — {wins}勝{losses}敗（{translate_rank(rank_str)}）')
            if lines:
                embed.add_field(name='🔥 目前幕內戰績前五名', value='\n'.join(lines), inline=False)
        else:
            embed.add_field(name='🏅 各級優勝', value='尚無資料（場所可能還沒開始，或番付表尚未收錄）', inline=False)
    embed.set_footer(text='資料來源：sumo-api.com')
    return embed

def build_guide_embed() -> discord.Embed:
    embed = discord.Embed(title='📖 Sumo Bot 使用說明', description='查詢大相撲力士資料與場所結果，支援日文漢字、羅馬拼音、常見繁中翻譯名。', color=BRAND_COLOR)
    embed.add_field(name='🔍 /rikishi', value='查詢單一力士完整資料（年齡、出身、部屋、番付、身體數據、生涯戰績、優勝與三賞次數）\n`name`：力士名稱（必填）\n範例：`/rikishi name:Onosato`', inline=False)
    embed.add_field(name='🔍 /record', value='查詢力士單一場所的逐日戰績\n`name`：力士名稱（必填）\n`basho`：場所代碼 YYYYMM（選填，不填則抓目前/最近一次場所）\n範例：`/record name:Hoshoryu basho:202607`', inline=False)
    embed.add_field(name='🔍 /h2h', value='查詢兩位力士的對戰紀錄與勝負統計\n`name1`、`name2`：兩位力士名稱（皆必填）\n範例：`/h2h name1:Aonishiki name2:Hoshoryu`', inline=False)
    embed.add_field(name='🔍 /basho', value='查詢場所結果（各級優勝、三賞）\n`basho`：場所代碼 YYYYMM（選填，不填則抓目前/最近一次場所）\n範例：`/basho basho:202605`', inline=False)
    embed.add_field(name='🗨️ 名稱查詢小技巧', value='支援大小寫不拘的力士羅馬拼音名，如有四股名同姓情形，建議使用全名。支援的日文漢字與繁中搜尋，如 Onosato 寫作`大の里`、`大之里`持續更新中，可查閱 Github 的 json 檔，如想完善也歡迎向作者反應。', inline=False)
    embed.add_field(name='🗨️ 感謝', value='若想支持，本機器人基於`sumo-api.com`的免費 api 運作，可以支持他們。', inline= False)
    embed.set_footer(text='資料來源：sumo-api.com')
    return embed
