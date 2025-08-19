import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

GUILD_ID = 1108759661051650138
TARGET_USER_ID = 1401152015551434802
ROLE_NAMES = {
    "1": "斉昭用#1",
    "2": "斉昭用#2",
    "3": "斉昭用#3",
    "4": "斉昭用#4"
}
CHANNEL_IDS = [1400485670321000510, 1367045548653416518]
TEMP_RECORD = 41.8
RECORD_HOLDER = "群馬県伊勢崎"
RECORD_TEXT = f"国内観測史上最高気温の{RECORD_HOLDER}{TEMP_RECORD}度を更新しました。"

class AutoRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_role_change = None
        self.notified_temps = {}
        self.check_conditions.start()

    def cog_unload(self):
        self.check_conditions.cancel()

    @tasks.loop(minutes=1)
    async def check_conditions(self):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            print("❌ GUILD がまだ取得できていません。次のループで再試行します。")
            return

        member = guild.get_member(TARGET_USER_ID)
        if member is None:
            print("❌ 対象ユーザーが見つかりません。")
            return

        try:
            async with aiohttp.ClientSession() as session:
                await self.check_earthquake_and_tsunami(session, member)
                await self.check_temperature(session, member)

                if self.scheduled_role_change and datetime.utcnow() >= self.scheduled_role_change:
                    await self.apply_role(member, ROLE_NAMES["1"], 1)
                    self.scheduled_role_change = None

        except Exception as e:
            print("⚠️ チェック中にエラーが発生しました:", e)

    async def check_earthquake_and_tsunami(self, session, member):
        async with session.get("https://www.data.jma.go.jp/developer/xml/eqvol.xml") as resp:
            eqvol_text = await resp.text()
        eqvol_fixed = str(BeautifulSoup(eqvol_text, "lxml"))
        root = ET.fromstring(eqvol_fixed)
        for item in root.findall(".//item"): 
            title = item.find("title").text
            if not title.startswith("震度速報") and "震度" in title:
                shindo = re.search(r"震度([5-7][弱強]?)", title)
                if shindo:
                    val = shindo.group(1)
                    if "5弱" in val:
                        if "津波の心配なし" in title:
                            self.scheduled_role_change = datetime.utcnow() + timedelta(hours=4)
                            print("🕒 斉昭用#1 に4時間後変更予定")
                        await self.apply_role(member, ROLE_NAMES["2"], 2)
                    elif val in ["5強", "6弱", "6強"]:
                        await self.apply_role(member, ROLE_NAMES["3"], 3)
                    elif val == "7":
                        await self.apply_role(member, ROLE_NAMES["4"], 4)

        async with session.get("https://www.data.jma.go.jp/developer/xml/wfs.xml") as resp:
            tsunami_text = await resp.text()
        tsunami_fixed = str(BeautifulSoup(tsunami_text, "lxml"))
        root = ET.fromstring(tsunami_fixed)
        for item in root.findall(".//item"):
            title = item.find("title").text
            if "津波警報" in title:
                await self.apply_role(member, ROLE_NAMES["3"], 3)
            elif "大津波警報" in title:
                await self.apply_role(member, ROLE_NAMES["4"], 4)

        async with session.get("https://www.data.jma.go.jp/developer/xml/warn.xml") as resp:
            warn_text = await resp.text()
        warn_fixed = str(BeautifulSoup(warn_text, "lxml"))
        root = ET.fromstring(warn_fixed)
        for item in root.findall(".//item"):
            title = item.find("title").text
            if "特別警報" in title:
                await self.apply_role(member, ROLE_NAMES["4"], 4)

    async def check_temperature(self, session, member):
        over_40 = 0
        async with session.get("https://tenki.jp/amedas/") as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.obs-table tbody tr")
        now = datetime.now()

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
            location = cols[0].text.strip()
            temp_text = cols[1].text.strip().replace("℃", "")
            time_text = cols[4].text.strip()
            try:
                temp = float(temp_text)
            except:
                continue
            if temp >= 40.0:
                over_40 += 1
                key = f"{location}_{time_text}"
                if key not in self.notified_temps or temp > self.notified_temps[key]:
                    self.notified_temps[key] = temp
                    msg = f"【気温情報】{location}で気温が{temp}度を観測しました ({time_text})"
                    if temp > TEMP_RECORD:
                        msg += f"\n{RECORD_TEXT}"
                    await self.send_to_channels(msg)

        if now.hour <= 11:
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue
                temp_text = cols[1].text.strip().replace("℃", "")
                try:
                    temp = float(temp_text)
                except:
                    continue
                if temp >= 36.0:
                    await self.apply_role(member, ROLE_NAMES["2"], 2)
                    break

        if over_40 >= 5:
            await self.apply_role(member, ROLE_NAMES["3"], 3)

    async def apply_role(self, member, role_name, level):
        guild = member.guild
        target_role = discord.utils.get(guild.roles, name=role_name)
        if not target_role:
            return

        role_names = {"斉昭用#1", "斉昭用#2", "斉昭用#3", "斉昭用#4"}
        roles_to_remove = [r for r in member.roles if r.name in role_names and r != target_role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        if target_role not in member.roles:
            await member.add_roles(target_role)
            msg = f"{member.display_name} のロールを {role_name} に変更しました (条件#{level})"
            await self.send_to_channels(msg)

    async def send_to_channels(self, message):
        for cid in CHANNEL_IDS:
            channel = self.bot.get_channel(cid)
            if channel:
                await channel.send(message)

@commands.Cog.listener()
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

async def setup(bot):
    cog = AutoRoleCog(bot)
    bot.add_listener(on_command_error)
    await bot.add_cog(cog)