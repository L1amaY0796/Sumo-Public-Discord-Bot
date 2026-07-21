import os
from dotenv import load_dotenv
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEST_GUILD_ID = os.getenv('TEST_GUILD_ID') or None
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
CACHE_DEFAULT_TTL_SECONDS = float(os.getenv('CACHE_DEFAULT_TTL_SECONDS', '300'))
if not DISCORD_TOKEN:
    raise RuntimeError('找不到 DISCORD_TOKEN，請複製 .env.example 為 .env，並填入你的 Discord Bot Token。')
