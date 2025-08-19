import discord
from discord.ext import commands
import re

# 情報取得チャンネル
SOURCE_CHANNEL_ID = 1317456480777011290  

# 情報を送ってくるBOTのID
SOURCE_BOT_ID = 1317457246073917531  

# 送信先（サーバーBとCの通常テキストチャンネル）
TARGET_CHANNEL_IDS = [
    1400485670321000510,  # サーバーB
    1367045548653416518   # サーバーC
]

class EEWForwarder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 他のBOTのメッセージは無視するが、指定BOTだけ許可
        if message.author.bot and message.author.id != SOURCE_BOT_ID:
            return

        # 情報取得チャンネル以外は無視
        if message.channel.id != SOURCE_CHANNEL_ID:
            return

        # 埋め込みが含まれているか確認
        if not message.embeds:
            return

        embed = message.embeds[0]
        content = embed.description or ""

        # 緊急地震速報か確認
        if "緊急地震速報" not in content:
            return

        # 最大震度を抽出
        match = re.search(r"最大震度[:：]\s*([0-9]+)", content)
        if not match:
            return

        max_intensity = int(match.group(1))

        # 震度3以上なら転送
        if max_intensity >= 3:
            for channel_id in TARGET_CHANNEL_IDS:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(EEWForwarder(bot))
