import unicodedata
from datetime import date, datetime
from typing import Optional
BASHO_MONTHS = [1, 3, 5, 7, 9, 11]
BASHO_NAMES = {1: '一月場所（初場所）', 3: '三月場所（春場所）', 5: '五月場所（夏場所）', 7: '七月場所（名古屋場所）', 9: '九月場所（秋場所）', 11: '十一月場所（九州場所）'}

def current_basho_id(today: Optional[date]=None) -> str:
    today = today or date.today()
    year = today.year
    month = today.month
    candidate_months = [m for m in BASHO_MONTHS if m <= month]
    if candidate_months:
        basho_month = max(candidate_months)
    else:
        basho_month = 11
        year -= 1
    return f'{year}{basho_month:02d}'

def basho_display_name(basho_id: str) -> str:
    try:
        year = int(basho_id[:4])
        month = int(basho_id[4:6])
        name = BASHO_NAMES.get(month, f'{month}月場所')
        return f'{year}年 {name}'
    except (ValueError, IndexError):
        return basho_id

def calc_age(birth_date_str: Optional[str], as_of: Optional[date]=None) -> Optional[int]:
    if not birth_date_str:
        return None
    as_of = as_of or date.today()
    try:
        birth = datetime.fromisoformat(birth_date_str.replace('Z', '+00:00')).date()
    except ValueError:
        try:
            birth = datetime.strptime(birth_date_str[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
    years = as_of.year - birth.year - ((as_of.month, as_of.day) < (birth.month, birth.day))
    return years
DIVISION_ZH = {'Yokozuna': '橫綱', 'Ozeki': '大關', 'Sekiwake': '關脇', 'Komusubi': '小結', 'Maegashira': '前頭', 'Juryo': '十兩', 'Makuuchi': '幕內', 'Makushita': '幕下', 'Sandanme': '三段目', 'Jonidan': '序二段', 'Jonokuchi': '序之口', 'Mae-zumo': '前相撲', 'Banzuke-gai': '番付外'}

def translate_rank(rank_en: Optional[str]) -> str:
    if not rank_en:
        return '不明'
    parts = rank_en.split(' ', 1)
    division = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    zh = DIVISION_ZH.get(division)
    if not zh:
        return rank_en
    return f'{zh} {rest}'.strip()

def translate_division(division_en: Optional[str]) -> str:
    if not division_en:
        return '不明'
    return DIVISION_ZH.get(division_en, division_en)

def parse_rank_string(rank_en: Optional[str]) -> tuple[str, str]:
    """把類似 'Maegashira 12 East' 拆成 ('Maegashira', '12')，拆不出號碼則回傳空字串。"""
    if not rank_en:
        return ('', '')
    parts = rank_en.split(' ')
    division = parts[0] if parts else ''
    number = parts[1] if len(parts) > 1 and parts[1].isdigit() else ''
    return (division, number)

def display_width(s: str) -> int:
    """等寬字型下的顯示寬度：全形/中日文字算 2，其餘算 1（用來對齊 code block 表格）。"""
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in s)

def pad_display(s: str, width: int) -> str:
    return s + ' ' * max(0, width - display_width(s))

# ---------- 錯誤訊息共用文字 ----------
GITHUB_REPO_URL = "https://github.com/L1amaY0796/Sumo-Public-Discord-Bot"
SUPPORT_EMAIL = "llamayong96@gmail.com"

SUPPORT_CONTACT_MESSAGE = (
    f"如果問題持續發生，歡迎到 GitHub 回報：{GITHUB_REPO_URL}\n"
    f"或寄信聯繫作者：{SUPPORT_EMAIL}"
)
