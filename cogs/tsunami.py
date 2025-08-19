import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# 通知先チャンネルID
TARGET_CHANNEL_IDS = [1367045548653416518, 1400485670321000510]

# JST
JST = timezone(timedelta(hours=9))

# 津波メッセージ定義
TSUNAMI_MESSAGES = {
    "MajorWarning": "【大津波警報】巨大な津波が押し寄せます。直ちに高台へ避難してください",
    "Warning": "【津波警報】直ちに海岸や河口付近からは離れ、高台へ避難してください",
    "Advisory": "【津波注意報】海岸・海中での作業は中止し、海岸から離れてください",
    "Forecast": "【津波予報（若干の海面変動）】若干の海面変動が予想されます。海の中へ入らず、海岸から離れてください",
}

FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml"

class TsunamiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_event_ids = set()
        self.check_tsunami.start()

    def cog_unload(self):
        self.check_tsunami.cancel()

    @tasks.loop(minutes=1)
    async def check_tsunami(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(FEED_URL) as resp:
                if resp.status != 200:
                    return
                xml_text = await resp.text()

        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            eid = entry.find("atom:id", ns).text
            title = entry.find("atom:title", ns).text

            if eid in self.last_event_ids:
                continue
            self.last_event_ids.add(eid)

            if "津波警報・注意報・予報" in title:
                await self.handle_tsunami_alert(entry.find("atom:link", ns).attrib["href"])

    async def handle_tsunami_alert(self, detail_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(detail_url) as resp:
                if resp.status != 200:
                    return
                xml_text = await resp.text()

        root = ET.fromstring(xml_text)
        ns = {"jmx": "http://xml.kishou.go.jp/jmaxml1/"}

        # 津波タグを探す
        tsunami_tags = root.findall(".//jmx:Tsunami", ns)
        if not tsunami_tags:
            return

        for tag in tsunami_tags:
            code = tag.attrib.get("type")  # MajorWarning / Warning / Advisory / Forecast
            message = TSUNAMI_MESSAGES.get(code, None)
            if message:
                embed = discord.Embed(
                    title="津波情報",
                    description=message,
                    color=discord.Color.blue(),
                    timestamp=datetime.now(JST)
                )
                for channel_id in TARGET_CHANNEL_IDS:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TsunamiCog(bot))
