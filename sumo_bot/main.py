import asyncio
import logging
import sys
import aiohttp
import discord
from discord.ext import commands
import config
from sumo_api import SumoAPI
import config
from sumo_api import SumoAPI
from utils import SUPPORT_CONTACT_MESSAGE

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
log = logging.getLogger('sumo_bot')
INTENTS = discord.Intents.default()

class SumoBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='!', intents=INTENTS)
        self.http_session: aiohttp.ClientSession | None = None
        self.sumo_api: SumoAPI | None = None

    async def setup_hook(self):
        self.http_session = aiohttp.ClientSession()
        self.sumo_api = SumoAPI(self.http_session, max_concurrent_requests=config.MAX_CONCURRENT_REQUESTS, default_ttl=config.CACHE_DEFAULT_TTL_SECONDS)
        log.info(f'SumoAPI 已啟用快取與併發限制：max_concurrent_requests={config.MAX_CONCURRENT_REQUESTS}, default_ttl={config.CACHE_DEFAULT_TTL_SECONDS}s')
        await self.load_extension('cogs.rikishi_cog')
        if config.TEST_GUILD_ID:
            guild = discord.Object(id=int(config.TEST_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info(f'已同步 {len(synced)} 個 slash command 到測試伺服器 {config.TEST_GUILD_ID}')
            self.tree.clear_commands(guild=None)
            global_synced = await self.tree.sync()
            log.info(f'已清除全域指令（目前全域指令數：{len(global_synced)}，預期為 0）')
        else:
            synced = await self.tree.sync()
            log.info(f'已同步 {len(synced)} 個 slash command（全域同步，可能需要等一段時間才會出現）')

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()
bot = SumoBot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    log.exception(f'指令 /{(interaction.command.name if interaction.command else '?')} 發生未預期的錯誤', exc_info=error)
    error_message = (
        f"⚠️ 指令執行時發生未預期的錯誤，內容已記錄，請稍後再試。\n{SUPPORT_CONTACT_MESSAGE}"
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    except discord.HTTPException:
        log.warning('連錯誤訊息都無法送出，可能是互動已逾時')

@bot.event
async def on_error(event_method: str, *args, **kwargs):
    log.exception(f'事件 {event_method} 發生未預期的錯誤')

@bot.event
async def on_ready():
    log.info(f'登入成功：{bot.user}（ID: {bot.user.id}）')

async def main():
    async with bot:
        await bot.start(config.DISCORD_TOKEN)
if __name__ == '__main__':
    asyncio.run(main())
