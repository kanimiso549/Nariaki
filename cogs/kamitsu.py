import discord
from discord.ext import commands
import random

GUILD_ID = 876782808847220786  # サーバー限定
TARGET_CHANNEL_ID = 1403576370063478814  # 画像が送信されているチャンネルID

class Kamitsu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot自身のメッセージは無視
        if message.author.bot:
            return

        # サーバー制限
        if message.guild is None or message.guild.id != GUILD_ID:
            return

        # コマンド判定（完全一致）
        if message.content.strip().lower() == "/kamitsu":
            channel = self.bot.get_channel(TARGET_CHANNEL_ID)
            if not channel:
                await message.reply("対象チャンネルが見つかりません。", mention_author=True)
                return

            images = []
            async for msg in channel.history(limit=200):
                for attachment in msg.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        images.append(attachment.url)

            if not images:
                await message.reply("画像が見つかりませんでした。", mention_author=True)
                return

            selected_image = random.choice(images)
            await message.reply(selected_image, mention_author=True)

async def setup(bot):
    await bot.add_cog(Kamitsu(bot))
