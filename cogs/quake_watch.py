import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import asyncio

FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"

TARGET_CHANNEL_IDS = [1400485670321000510, 1367045548653416518]
CONFIRM_CHANNEL_ID = 1317456480777011290  # 承認用チャンネル

class ApproveView(discord.ui.View):
    def __init__(self, bot, embed):
        super().__init__(timeout=600)  # 10分でタイムアウト
        self.bot = bot
        self.embed = embed

    @discord.ui.button(label="承認して送信", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 承認されたらターゲットチャンネルへ送信
        for channel_id in TARGET_CHANNEL_IDS:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=self.embed)

        await interaction.response.send_message("✅ 承認されました。通知を送信しました。", ephemeral=True)
        self.stop()


class QuakeWatch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.latest_id = None
        self.check_quake.start()

    def cog_unload(self):
        self.check_quake.cancel()

    @tasks.loop(minutes=1)
    async def check_quake(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(FEED_URL) as resp:
                text = await resp.text()
        root = ET.fromstring(text)

        # 最新のentryを取得
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            return

        eq_id = entry.find("atom:id", ns).text
        if eq_id == self.latest_id:
            return  # 既に処理済み
        self.latest_id = eq_id

        title = entry.find("atom:title", ns).text
        link = entry.find("atom:link", ns).attrib["href"]

        # 詳細XMLを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                detail_text = await resp.text()
        detail_root = ET.fromstring(detail_text)

        # 最大震度を取得
        max_int_elem = detail_root.find(".//MaxInt")
        if max_int_elem is None:
            return
        max_int = max_int_elem.text  # 例 "３" や "２"
        try:
            shindo = int(max_int.replace("弱","").replace("強",""))
        except:
            shindo = 0

        # 埋め込み生成
        embed = discord.Embed(
            title=f"【地震情報】{title}",
            description=f"詳細: [気象庁XML]({link})\n最大震度: {max_int}",
            color=discord.Color.red() if shindo >= 3 else discord.Color.orange()
        )

        # 判定
        if shindo >= 3:
            # 確認なしで通知
            for channel_id in TARGET_CHANNEL_IDS:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
        else:
            # 確認チャンネルにボタン付き送信
            confirm_channel = self.bot.get_channel(CONFIRM_CHANNEL_ID)
            if confirm_channel:
                await confirm_channel.send(
                    content="⚠️ 震度1〜2の地震がありました。承認後に通知を送ります。",
                    embed=embed,
                    view=ApproveView(self.bot, embed)
                )

    @check_quake.before_loop
    async def before_quake(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(QuakeWatch(bot))
