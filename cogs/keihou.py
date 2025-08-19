# cogs/weather_alerts.py
import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import feedparser
from datetime import datetime, timezone, timedelta

TARGET_CHANNEL_IDS = [1367045548653416518, 1400485670321000510]
LOG_CHANNEL_ID = 1328386190231081084

JST = timezone(timedelta(hours=9))


class WeatherAlerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_alerts.start()

    def cog_unload(self):
        self.check_alerts.cancel()

    async def fetch_xml(self, session, url):
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception as e:
            print(f"XML fetch error: {e}")
        return None

    @tasks.loop(minutes=1)
    async def check_alerts(self):
        async with aiohttp.ClientSession() as session:
            # === 土砂災害警戒情報 ===
            xml_data = await self.fetch_xml(session, "https://www.data.jma.go.jp/developer/xml/feed/extra.xml")
            if xml_data:
                feed = feedparser.parse(xml_data)
                for entry in feed.entries:
                    if "土砂災害警戒情報" in entry.title:
                        detail_xml = await self.fetch_xml(session, entry.link)
                        if not detail_xml:
                            continue
                        root = ET.fromstring(detail_xml)

                        area = root.findtext(".//Area/Name")
                        status = root.findtext(".//Status")

                        if not area or not status:
                            continue  # 情報不足なら送信しない

                        embed = discord.Embed(
                            title="【土砂災害警戒情報】",
                            description=f"{area}で{status}されました。",
                            color=discord.Color.orange(),
                            timestamp=datetime.now(JST)
                        )

                        for ch_id in TARGET_CHANNEL_IDS:
                            ch = self.bot.get_channel(ch_id)
                            if ch:
                                await ch.send(embed=embed)

            # === 顕著な大雨・大雪情報 ===
            xml_data = await self.fetch_xml(session, "https://www.data.jma.go.jp/developer/xml/feed/extra.xml")
            if xml_data:
                feed = feedparser.parse(xml_data)
                for entry in feed.entries:
                    if "顕著な大雨に関する情報" in entry.title:
                        detail_xml = await self.fetch_xml(session, entry.link)
                        if not detail_xml:
                            continue
                        root = ET.fromstring(detail_xml)
                        area = root.findtext(".//Area/Name")

                        if not area:
                            continue  # 情報不足なら送信しない

                        description = (
                            f"{area}では、線状降水帯による非常に激しい雨が同じ場所で降り続いています。\n"
                            "命に危険が及ぶ土砂災害や洪水による災害発生の危険度が急激に高まっています。"
                        )

                        embed = discord.Embed(
                            title="【顕著な大雨に関する情報】",
                            description=description,
                            color=discord.Color.blue(),
                            timestamp=datetime.now(JST)
                        )

                        for ch_id in TARGET_CHANNEL_IDS:
                            ch = self.bot.get_channel(ch_id)
                            if ch:
                                await ch.send(embed=embed)

                    elif "顕著な大雪に関する情報" in entry.title:
                        detail_xml = await self.fetch_xml(session, entry.link)
                        if not detail_xml:
                            continue
                        root = ET.fromstring(detail_xml)
                        area = root.findtext(".//Area/Name")
                        snowfall = root.findtext(".//Snowfall")
                        end_time = root.findtext(".//EndTime")

                        if not area or not snowfall or not end_time:
                            continue  # 情報不足なら送信しない

                        description = (
                            f"{area}で{snowfall}センチの顕著な降雪を観測しました。\n"
                            f"この強い雪は{end_time}まで続く見込みです。\n"
                            f"{area}では、深刻な交通障害の発生するおそれが高まっています。"
                        )

                        embed = discord.Embed(
                            title="【顕著な大雪に関する情報】",
                            description=description,
                            color=discord.Color.teal(),
                            timestamp=datetime.now(JST)
                        )

                        for ch_id in TARGET_CHANNEL_IDS:
                            ch = self.bot.get_channel(ch_id)
                            if ch:
                                await ch.send(embed=embed)

            # === 梅雨入り・梅雨明け情報 ===
            xml_data = await self.fetch_xml(session, "https://www.data.jma.go.jp/developer/xml/feed/extra.xml")
            if xml_data:
                feed = feedparser.parse(xml_data)
                for entry in feed.entries:
                    if "梅雨入り" in entry.title or "梅雨明け" in entry.title:
                        area = entry.title.split()[0] if entry.title else None
                        if not area:
                            continue

                        embed = discord.Embed(
                            title=f"【{entry.title}】",
                            description=f"{area}地方は{entry.title}したと見られます。",
                            color=discord.Color.green(),
                            timestamp=datetime.now(JST)
                        )

                        for ch_id in TARGET_CHANNEL_IDS:
                            ch = self.bot.get_channel(ch_id)
                            if ch:
                                await ch.send(embed=embed)

            # === 記録的短時間大雨情報 ===
            xml_data = await self.fetch_xml(session, "https://www.data.jma.go.jp/developer/xml/feed/extra.xml")
            if xml_data:
                feed = feedparser.parse(xml_data)
                for entry in feed.entries:
                    if "記録的短時間大雨情報" in entry.title:
                        detail_xml = await self.fetch_xml(session, entry.link)
                        if not detail_xml:
                            continue
                        root = ET.fromstring(detail_xml)

                        time = root.findtext(".//Time")
                        areas = root.findall(".//Area")

                        if not time or not areas:
                            continue  # 情報不足なら送信しない

                        lines = []
                        for a in areas:
                            name = a.findtext("Name")
                            rainfall = a.findtext("Rainfall")
                            if name and rainfall:
                                lines.append(f"{name}で{rainfall}ミリ")
                        if not lines:
                            continue

                        description = f"{time}までの１時間で\n" + "\n".join(lines) + "\nの解析雨量。"

                        embed = discord.Embed(
                            title="【記録的短時間大雨情報】",
                            description=description,
                            color=discord.Color.purple(),
                            timestamp=datetime.now(JST)
                        )

                        for ch_id in TARGET_CHANNEL_IDS:
                            ch = self.bot.get_channel(ch_id)
                            if ch:
                                await ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WeatherAlerts(bot))
