import discord
from discord.ext import commands

# 設定
ALLOWED_ROLE_IDS = [1008232882755620946]  # 許可ロールID（int型で）
RESPONSE_MESSAGE = "ヤリチンさん、やめてください"
TRIGGER_KEYWORDS = ["sex!!", "中に出す", "ﾍｺﾍｺ", "ざぁ～こ♡ざぁ～こ♡", "誰ヤリ定期", "犯す"]

class Yarichin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # botやDMは無視
        if message.author.bot or not message.guild:
            return

        # 指定ロールを持っているか
        user_role_ids = [role.id for role in message.author.roles]
        if not any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids):
            return

        # キーワードチェック
        content = message.content.lower()
        if any(keyword.lower() in content for keyword in TRIGGER_KEYWORDS):
            # メンション付き返信のみ
            await message.reply(RESPONSE_MESSAGE, mention_author=True)

async def setup(bot):
    await bot.add_cog(Yarichin(bot))
