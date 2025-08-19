import discord
from discord import app_commands
from discord.ext import commands
import random

SOURCE_CHANNEL_ID = 1401178254441971712
MEDIA_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".webm", ".mkv"]

class Kasso(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.media_cache = []

    async def fetch_media_files(self):
        channel = self.bot.get_channel(SOURCE_CHANNEL_ID)
        if not channel:
            print("⚠️ 指定チャンネルが見つかりません。")
            return
        media_files = []
        try:
            async for msg in channel.history(limit=200):
                for att in msg.attachments:
                    if any(att.filename.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
                        media_files.append(att)
        except Exception as e:
            print(f"❌ ファイル取得エラー: {e}")
        self.media_cache = media_files
        print(f"📦 {len(media_files)} 件のファイルをキャッシュしました")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.fetch_media_files()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != SOURCE_CHANNEL_ID:
            return
        for att in message.attachments:
            if any(att.filename.lower().endswith(ext) for ext in MEDIA_EXTENSIONS):
                self.media_cache.append(att)
                print(f"📥 新しいメディアを追加: {att.filename}")

    @app_commands.command(name="kasso", description="人呼べよ")
    async def send_random_media(self, interaction: discord.Interaction):
        if not self.media_cache:
            await self.fetch_media_files()
        if not self.media_cache:
            await interaction.response.send_message("⚠️ 利用可能なメディアファイルがありません。", ephemeral=True)
            return
        media = random.choice(self.media_cache)
        try:
            await interaction.response.send_message(file=await media.to_file())
        except Exception as e:
            await interaction.response.send_message(f"❌ 送信エラー: {e}", ephemeral=True)

    @app_commands.command(name="reloadmedia", description="ファイルキャッシュを再読み込みします")
    async def reload_cache(self, interaction: discord.Interaction):
        await self.fetch_media_files()
        await interaction.response.send_message("🔄 ファイルキャッシュを再読み込みしました。", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Kasso(bot))
