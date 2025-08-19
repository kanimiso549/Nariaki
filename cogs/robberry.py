import discord
from discord.ext import commands

# 設定
RESPONSE_MESSAGE = "あーあ"
TRIGGER_KEYWORDS = ["0XP!!!!!!!!!!!!!!!!!!!"]
TARGET_BOT_ID = 894191491277258752  # 対象BOTのユーザーID（整数）

class Robberry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # 自分のメッセージは無視
        if message.author == self.bot.user:
            return
        
        # BOT以外は無視
        if message.author.id != TARGET_BOT_ID:
            return

        # キーワードチェック（大文字小文字区別なし）
        content = message.content.lower()
        if any(keyword.lower() in content for keyword in TRIGGER_KEYWORDS):
            # メンション付き返信のみ
            await message.reply(RESPONSE_MESSAGE, mention_author=True)

async def setup(bot):
    await bot.add_cog(Robberry(bot))
