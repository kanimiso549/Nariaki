import discord
from discord.ext import commands

DISCORD_TOKEN = ""  
LOG_CHANNEL_ID = 1401186153809580032

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Cog一覧
EXTENSIONS = [
    "cogs.amedas_monitor",
    "cogs.auto_role_cog_lxml_fixed",
    "cogs.emergency_alert_buttons",
    "cogs.free_message",
    "cogs.jishin",
    "cogs.EEW",
    "cogs.kamitsu",
    "cogs.kasso",
    "cogs.monday_reminder",
    # "cogs.warning",
    "cogs.resync",
    "cogs.rieki",
    "cogs.robberry",
    "cogs.say_command",
    "cogs.shindo",
    "cogs.switch_role",
    "cogs.yarichin",
    "cogs.meme",
    "cogs.yoroshii",
    "cogs.chono",
    "cogs.quake_watch",
    "cogs.tsunami",
    "cogs.keihou",
    "cogs.wopper"
]

@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user}")

@bot.event
async def setup_hook():
    bot.log_channel_id = LOG_CHANNEL_ID

    # ===== 二重登録解消処理 =====
    target_guild_id = 876782808847220786
    print("🗑 重複防止のためギルドコマンド削除中…")
    bot.tree.clear_commands(guild=discord.Object(id=target_guild_id))
    await bot.tree.sync(guild=discord.Object(id=target_guild_id))
    # ==========================

    # Cog読み込み
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")

    # グローバル登録
    synced = await bot.tree.sync()
    print(f"🔧 Synced {len(synced)} global commands")

bot.run(DISCORD_TOKEN)
