import discord
from discord.ext import commands

# 設定
ALLOWED_ROLE_IDS = [1008232882755620946]  # 許可ロールID（int型で）
RESPONSE_MESSAGE = "https://cdn.discordapp.com/attachments/1400485670321000510/1407360986440269844/e145f2eaa98acfda.mp4?ex=68a5d28e&is=68a4810e&hm=9e9175c8fea6a3706f519c6d8058f5fd13d1427bb581c567a3a9892be9bb7b3d&"
TRIGGER_KEYWORDS = ["ワッパー", "ZIPPO", "児ポ", "㌔㍉"]

class Wopper(commands.Cog):
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
    await bot.add_cog(Wopper(bot))
