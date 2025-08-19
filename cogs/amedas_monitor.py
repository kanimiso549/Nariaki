import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import re

TARGET_CHANNEL_IDS = [1400485670321000510, 1367045548653416518]
REC_TEMP = 41.8
REC_LOC = "群馬県伊勢崎"

class AmedasFullMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notified = {}
        self.check_temp.start()

    def cog_unload(self):
        self.check_temp.cancel()

    @tasks.loop(minutes=1)
    async def check_temp(self):
        url = "https://tenki.jp/amedas/ranking/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            items = soup.select(".ranking-list li")

            for li in items:
                # 地点名、気温、観測時間の取得
                name_tag = li.select_one(".left-style span")
                temp_tag = li.select_one(".value span")
                time_tag = li.select_one(".time")

                if not (name_tag and temp_tag and time_tag):
                    continue

                name = name_tag.text.strip()  # 例: "埼玉県熊谷"
                temp_str = temp_tag.text.strip().replace("℃", "")
                time_str = time_tag.text.strip().replace("（", "").replace("）", "")  # 例: "14時30分"

                try:
                    temp = float(temp_str)
                except ValueError:
                    continue

                prev = self.notified.get(name, 0.0)
                if temp > 40.0 and temp > prev:
                    self.notified[name] = temp
                    msg = f"【気温情報】{name}で気温が{temp}度を観測しました（{time_str}）。"
                    if temp > REC_TEMP:
                        msg += f"\n国内観測史上最高気温の{REC_LOC}{REC_TEMP}度を更新しました。"
                    for cid in TARGET_CHANNEL_IDS:
                        ch = self.bot.get_channel(cid)
                        if ch:
                            await ch.send(msg)

        except Exception as e:
            print(f"気温チェック中にエラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(AmedasFullMonitor(bot))
