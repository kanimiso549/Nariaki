import discord
from discord import app_commands
from discord.ext import commands
import random
import aiohttp
import io

TARGET_CHANNEL_ID = 1401584838581944451
ALLOWED_ROLE_ID = 1084660531559944302

MEDIA_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mov", ".webm", ".mkv"
]

def has_allowed_role(interaction: discord.Interaction) -> bool:
    """指定ロールを持っているか確認"""
    return any(role.id == ALLOWED_ROLE_ID for role in interaction.user.roles)

class Rieki(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.media_file_cache = []  # URLとファイル名を保持

    async def fetch_media_files(self):
        """指定チャンネルからメディアURLとファイル名をキャッシュ"""
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if not channel:
            print("❌ チャンネルが見つかりません")
            return
        self.media_file_cache.clear()
        try:
            async for msg in channel.history(limit=200):
                for attachment in msg.attachments:
                    filename = attachment.filename.lower()
                    if any(filename.endswith(ext) for ext in MEDIA_EXTENSIONS):
                        self.media_file_cache.append((attachment.url, attachment.filename))
            print(f"🎞️ メディアファイル {len(self.media_file_cache)} 件をキャッシュしました。")
        except Exception as e:
            print(f"❌ メディア取得エラー: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.fetch_media_files()

    @app_commands.command(name="rieki", description="利益となりなさい")
    @app_commands.check(has_allowed_role)
    async def random_media(self, interaction: discord.Interaction):
        """ランダムにメディアを送信"""
        if not self.media_file_cache:
            await self.fetch_media_files()
        if not self.media_file_cache:
            await interaction.response.send_message("⚠️ メディアファイルが見つかりません。", ephemeral=True)
            return

        media_url, filename = random.choice(self.media_file_cache)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(media_url) as resp:
                    if resp.status != 200:
                        await interaction.response.send_message("⚠️ ファイルの取得に失敗しました。", ephemeral=True)
                        return
                    data = io.BytesIO(await resp.read())
                    await interaction.response.send_message(file=discord.File(data, filename=filename))
        except Exception as e:
            await interaction.response.send_message(f"❌ 送信エラー: {e}", ephemeral=True)

    @app_commands.command(name="reloadfiles", description="メディアファイルを再読み込みします")
    @app_commands.check(has_allowed_role)
    async def reload_files(self, interaction: discord.Interaction):
        await self.fetch_media_files()
        await interaction.response.send_message("🔄 メディアファイル一覧を再読み込みしました。", ephemeral=True)

    @random_media.error
    @reload_files.error
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("🚫 あなたにはこのコマンドを使う権限がありません。", ephemeral=True)
        else:
            raise error

async def setup(bot: commands.Bot):
    await bot.add_cog(Rieki(bot))
