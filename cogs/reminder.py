import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone, timedelta

TARGET_CHANNEL_IDS = [1400485670321000510, 1367045548653416518]  # サーバーB, C
FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"

# -------------------
# パーサ関数群（固定フォーマット整形用）
# -------------------
def parse_landslide(content: str):
    m = re.search(r"【(.+?)土砂災害警戒情報】", content)
    if not m:
        return None
    area = m.group(1)
    if "解除" in content:
        return f"【土砂災害警戒情報】{area}の土砂災害警戒情報は解除されました"
    else:
        return f"【土砂災害警戒情報】{area}に土砂災害警戒情報が発表されました"


def parse_tokubetsu(content: str):
    m = re.search(r"【(.+?)(.+?特別警報)】", content)
    if not m:
        return None
    area, warn = m.group(1), m.group(2)

    if "引き下げ" in content:
        return f"【特別警報】{area}の{warn}は引き下げられました"
    elif "解除" in content:
        return f"【特別警報】{area}の{warn}は解除されました"
    else:
        return f"【特別警報】{area}に{warn}が発表されました"


def parse_record_rain(content: str):
    m = re.search(r"(\d{1,2})時(\d{1,2})分\s+(.+?)で記録的短時間大雨\s+(.+?)付近で(\d+)ミリ", content)
    if not m:
        return None
    hh, mm, area, place, amount = m.groups()
    return f"【記録的短時間大雨情報】{hh}時{mm}分 {area}で記録的短時間大雨 {place}で{amount}ミリ"


def parse_extreme_rain(content: str):
    m = re.search(r"【顕著な大雨に関する情報】(.+?)では", content)
    if m:
        area = m.group(1)
        return (f"【顕著な大雨に関する情報】{area}では、線状降水帯による非常に激しい雨が"
                "同じ場所で降り続いています。命に危険が及ぶ土砂災害や洪水による"
                "災害発生の危険度が急激に高まっています。")
    return None


def parse_extreme_snow(content: str):
    m = re.search(r"【顕著な大雪に関する情報】(.+?)では、(\d+)日(\d{1,2})時までの(\d+)時間に(\d+)センチ", content)
    if m:
        area, day, hh, hours, snow = m.groups()
        return (f"【顕著な大雪に関する情報】{area}では、{day}日{hh}時までの{hours}時間に"
                f"{snow}センチの顕著な大雪を観測しました。この強い雪は今後も続く見込みです。"
                f"{area}では、大規模な交通障害の発生するおそれが高まっています。")
    return None


def parse_rainy_season(content: str):
    m = re.search(r"【梅雨の時期に関する情報】(.+)", content)
    if m:
        return f"【梅雨の時期に関する情報】{m.group(1)}"
    return None


# -------------------
# Cog本体
# -------------------
class WeatherAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.posted_ids = set()
        self.check_feed.start()

    def cog_unload(self):
        self.check_feed.cancel()

    @tasks.loop(minutes=1)
    async def check_feed(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(FEED_URL) as resp:
                if resp.status != 200:
                    return
                text = await resp.text()
                root = ET.fromstring(text)

                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    entry_id = entry.find("{http://www.w3.org/2005/Atom}id").text
                    if entry_id in self.posted_ids:
                        continue

                    updated_str = entry.find("{http://www.w3.org/2005/Atom}updated").text
                    updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)

                    # 2分以内のものだけ送信対象
                    if (now - updated) > timedelta(minutes=2):
                        continue

                    title = entry.find("{http://www.w3.org/2005/Atom}title").text
                    content = entry.find("{http://www.w3.org/2005/Atom}content").text

                    msg = None
                    if "土砂災害警戒情報" in title:
                        msg = parse_landslide(content)
                    elif "特別警報" in title:
                        msg = parse_tokubetsu(content)
                    elif "記録的短時間大雨情報" in title:
                        msg = parse_record_rain(content)
                    elif "顕著な大雨" in title:
                        msg = parse_extreme_rain(content)
                    elif "顕著な大雪" in title:
                        msg = parse_extreme_snow(content)
                    elif "梅雨" in title:
                        msg = parse_rainy_season(content)

                    if msg:
                        self.posted_ids.add(entry_id)  # 送信済みに記録
                        for channel_id in TARGET_CHANNEL_IDS:
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                await channel.send(msg)


async def setup(bot):
    await bot.add_cog(WeatherAlerts(bot))
