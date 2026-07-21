import discord
from discord import app_commands
from discord.ext import commands
from sumo_api import SumoAPI, SumoAPIError
from name_resolver import resolve_rikishi
from utils import current_basho_id, basho_display_name
import embeds
from sumo_api import SumoAPI, SumoAPIError
from name_resolver import resolve_rikishi
from utils import current_basho_id, basho_display_name, SUPPORT_CONTACT_MESSAGE
import embeds

class RikishiCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def api(self) -> SumoAPI:
        return self.bot.sumo_api

    async def _resolve_or_reply(self, interaction: discord.Interaction, query: str):
        try:
            rikishi = await resolve_rikishi(self.api, query)
        except SumoAPIError as e:
            await interaction.followup.send(f'⚠️ 查詢 sumo-api.com 時發生錯誤：{e}')
            return None
        if not rikishi:
            await interaction.followup.send(f'❌ 找不到「{query}」這位力士。\n可以試試：日文漢字（如 大の里）、羅馬拼音（如 Onosato）、或常見繁中翻譯名（如 大之里）。若確定是現役力士但查不到，可能是別名表裡還沒收錄，歡迎去 `sumo_bot/aliases.json` 補上。')
            return None
        return rikishi

    @app_commands.command(name='rikishi', description='查詢單一力士的完整資料（年齡、出身、部屋、番付、身體數據等）')
    @app_commands.describe(name='力士名稱（可用日文原名、羅馬拼音或繁中翻譯名）')
    async def rikishi(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        rikishi_data = await self._resolve_or_reply(interaction, name)
        if not rikishi_data:
            return
        rikishi_id = rikishi_data.get('id')
        try:
            full = await self.api.get_rikishi(rikishi_id)
            stats = await self.api.get_rikishi_stats(rikishi_id)
        except SumoAPIError as e:
            await interaction.followup.send(f'⚠️ 取得力士詳細資料時發生錯誤：{e}')
            return
        merged = {**rikishi_data, **full, 'id': rikishi_id}
        embed = embeds.build_rikishi_embed(merged, stats)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='record', description='查詢力士單一場所的逐日戰績（預設為目前/最近一次場所）')
    @app_commands.describe(name='力士名稱（日文原名／羅馬拼音／繁中翻譯名）', basho='場所代碼，格式 YYYYMM，例如 202607（不填則自動抓目前或最近一次場所）')
    async def record(self, interaction: discord.Interaction, name: str, basho: str | None=None):
        await interaction.response.defer()
        rikishi_data = await self._resolve_or_reply(interaction, name)
        if not rikishi_data:
            return
        basho_id = basho.strip() if basho else current_basho_id()
        if not (basho_id.isdigit() and len(basho_id) == 6):
            await interaction.followup.send('⚠️ 場所代碼格式錯誤，請用 YYYYMM，例如 202607（2026年七月場所）。')
            return
        rikishi_id = rikishi_data.get('id')
        try:
            matches = await self.api.get_rikishi_matches(rikishi_id, basho_id=basho_id)
        except SumoAPIError as e:
            await interaction.followup.send(f'⚠️ 取得戰績時發生錯誤：{e}')
            return
        embed = embeds.build_record_embed(rikishi_data, basho_id, matches)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='h2h', description='查詢兩位力士的對戰紀錄（例如兩位橫綱之間的交手成績）')
    @app_commands.describe(name1='力士一', name2='力士二')
    async def h2h(self, interaction: discord.Interaction, name1: str, name2: str):
        await interaction.response.defer()
        rikishi_a = await self._resolve_or_reply(interaction, name1)
        if not rikishi_a:
            return
        rikishi_b = await self._resolve_or_reply(interaction, name2)
        if not rikishi_b:
            return
        try:
            matches = await self.api.get_head_to_head(rikishi_a.get('id'), rikishi_b.get('id'))
        except SumoAPIError as e:
            await interaction.followup.send(f'⚠️ 取得對戰紀錄時發生錯誤：{e}')
            return
        embed = embeds.build_h2h_embed(rikishi_a, rikishi_b, matches)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='basho', description='查詢場所結果（優勝、三賞），不填代碼則查目前/最近一次場所')
    @app_commands.describe(basho='場所代碼，格式 YYYYMM，例如 202607（不填則自動抓目前或最近一次場所）')
    async def basho(self, interaction: discord.Interaction, basho: str | None=None):
        await interaction.response.defer()
        basho_id = basho.strip() if basho else current_basho_id()
        if not (basho_id.isdigit() and len(basho_id) == 6):
            await interaction.followup.send('⚠️ 場所代碼格式錯誤，請用 YYYYMM，例如 202607（2026年七月場所）。')
            return
        try:
            data = await self.api.get_basho(basho_id)
        except SumoAPIError as e:
            await interaction.followup.send(
                f"⚠️ 查不到 {basho_display_name(basho_id)} 的資料：{e}\n"
                f"（有可能該場所還沒有任何結果被寫進資料庫）\n{SUPPORT_CONTACT_MESSAGE}"
            )
            return
        banzuke = None
        if not data.get('yusho'):
            try:
                banzuke = await self.api.get_banzuke(basho_id, 'Makuuchi')
            except SumoAPIError:
                banzuke = None
        embed = embeds.build_basho_embed(basho_id, data, banzuke)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='guide', description='顯示所有指令的使用說明')
    async def guide(self, interaction: discord.Interaction):
        embed = embeds.build_guide_embed()
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(RikishiCog(bot))
