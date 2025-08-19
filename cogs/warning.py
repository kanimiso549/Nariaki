import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone, timedelta

TARGET_CHANNEL_IDS = [1367045548653416518, 1400485670321000510]
LOG_CHANNEL_ID = 1328386190231081084
EXECUTOR_LOG_CHANNEL_ID = 1404648254452400179  # 実行者IDログ

# JST
JST = timezone(timedelta(hours=9))

# 都道府県リスト
PREF_LIST = [
    "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
    "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
    "新潟県","富山県","石川県","福井県","山梨県","長野県",
    "岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県",
    "奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県",
    "徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県",
    "熊本県","大分県","宮崎県","鹿児島県","沖縄県"
]

DEBUG_LOG = True

class DisasterWeather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_ids = set()
        self.sent_dosha = {}
        self.sent_dosha_released = set()
        self.sent_warning = {}
        self.sent_warning_released = set()
        self.check_feed.start()

    def cog_unload(self):
        self.check_feed.cancel()

    async def _log(self, text):
        if not DEBUG_LOG:
            return
        try:
            ch = self.bot.get_channel(LOG_CHANNEL_ID) or await self.bot.fetch_channel(LOG_CHANNEL_ID)
            if ch:
                await ch.send(text)
            else:
                print("[JMA LOG]", text)
        except Exception as e:
            print("[JMA LOG ERROR]", e, text)

    async def _exec_log(self):
        """実行者IDログ"""
        try:
            ch = self.bot.get_channel(EXECUTOR_LOG_CHANNEL_ID) or await self.bot.fetch_channel(EXECUTOR_LOG_CHANNEL_ID)
            if ch:
                await ch.send(str(self.bot.user.id))  # メンションなし
        except Exception as e:
            await self._log(f"[EXECUTOR LOG ERROR] {e}")

    async def fetch_pref_from_detail(self, link_url):
        if not link_url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link_url, timeout=10) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        return None

            try:
                root = ET.fromstring(text)
            except Exception:
                for p in PREF_LIST:
                    if p in text:
                        return p
                return None

            for elem in root.iter():
                tag = elem.tag
                local = tag.rsplit("}", 1)[-1] if "}" in tag else tag
                if local.lower().find("area") != -1:
                    codeType = elem.attrib.get("codeType", "") or elem.attrib.get("codetype", "")
                    if "Pref" in codeType or "pref" in codeType or "都道府県" in codeType:
                        for child in elem:
                            cname = child.tag.rsplit("}", 1)[-1].lower()
                            if "name" in cname:
                                txt = (child.text or "").strip()
                                for p in PREF_LIST:
                                    if p in txt:
                                        return p
            for elem in root.iter():
                local = elem.tag.rsplit("}", 1)[-1] if "}" in elem.tag else elem.tag
                if "name" in local.lower():
                    txt = (elem.text or "").strip()
                    if txt:
                        for p in PREF_LIST:
                            if p in txt:
                                return p
            for p in PREF_LIST:
                if p in text:
                    return p
            return None

        except Exception as e:
            await self._log(f"[DEBUG] fetch_pref_from_detail exception: {e} url={link_url}")
            return None

    @tasks.loop(seconds=60)
    async def check_feed(self):
        await self._log("[JMA] フィードチェック開始")
        url = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        return
                    text = await resp.text()
            root = ET.fromstring(text)
            now = datetime.now(JST)

            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title") or ""
                id_ = entry.findtext("{http://www.w3.org/2005/Atom}id") or ""
                updated = entry.findtext("{http://www.w3.org/2005/Atom}updated") or ""
                link_url = None
                for link_el in entry.findall("{http://www.w3.org/2005/Atom}link"):
                    href = link_el.attrib.get("href")
                    ltype = link_el.attrib.get("type", "")
                    if ltype == "application/xml":
                        link_url = href
                        break
                    if href and href.endswith(".xml"):
                        link_url = href
                if not title or not id_ or not updated:
                    continue
                if id_ in self.sent_ids:
                    continue
                try:
                    updated_dt = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(JST)
                except Exception:
                    continue
                diff = (now - updated_dt).total_seconds()
                if diff < -60 or diff > 180:
                    continue

                # 土砂災害警戒情報
                if "土砂災害警戒情報" in title:
                    pref = await self.fetch_pref_from_detail(link_url) or self._pref_from_text(title)
                    if not pref:
                        continue
                    content_text = entry.findtext("{http://www.w3.org/2005/Atom}content") or ""
                    is_release = "全警戒解除" in content_text or "解除" in title
                    if is_release:
                        if pref in self.sent_dosha and pref not in self.sent_dosha_released:
                            await self._send_to_info(f"【土砂災害警戒情報】{pref}の土砂災害警戒情報が解除されました")
                            self.sent_dosha_released.add(pref)
                            self.sent_dosha.pop(pref, None)
                            self.sent_ids.add(id_)
                            await self._exec_log()
                    else:
                        if pref not in self.sent_dosha:
                            await self._send_to_info(f"【土砂災害警戒情報】{pref}に土砂災害警戒情報が発表、または更新されました")
                            self.sent_dosha[pref] = id_
                            self.sent_ids.add(id_)
                            await self._exec_log()

                # 特別警報
                elif "特別警報" in title and "注意報" not in title and "警報" in title:
                    pref = await self.fetch_pref_from_detail(link_url) or self._pref_from_text(title)
                    if not pref:
                        continue
                    kind_match = re.search(r"（?(.*?)特別警報", title)
                    kind = (kind_match.group(1) + "特別警報") if kind_match else "特別警報"
                    key = pref + kind
                    if "解除" in title:
                        if key in self.sent_warning and key not in self.sent_warning_released:
                            await self._send_to_info(f"【特別警報】{pref}の{kind}が解除されました")
                            self.sent_warning_released.add(key)
                            self.sent_warning.pop(key, None)
                            self.sent_ids.add(id_)
                            await self._exec_log()
                    else:
                        if key not in self.sent_warning:
                            await self._send_to_info(f"【特別警報】{pref}に{kind}が発表されました")
                            self.sent_warning[key] = id_
                            self.sent_ids.add(id_)
                            await self._exec_log()

                # 記録的短時間大雨情報
                elif "記録的短時間大雨情報" in title:
                    content = entry.findtext("{http://www.w3.org/2005/Atom}content") or ""

                    text = re.sub(r"^【.*?記録的短時間大雨情報】", "", content)

                    # 時刻抽出（例: １７時 or １７時３０分）
                    m = re.search(r"(\d{1,2})時(\d{0,2})?", text)
                    time_str = ""
                    if m:
                        hour = int(m.group(1))
                        minute = int(m.group(2) or 0)
                        time_str = f"{hour}時{minute:02d}分"
                        text = text[m.end():]  # 時刻部分を削除

                    # 全角数字を半角に
                    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))

                    result = f"【記録的短時間大雨情報】{time_str} {text.strip()}"
                    await self._send_to_info(result)
                    self.sent_ids.add(id_)
                    await self._exec_log()

                
                # 台風情報
                elif "台風" in title and "号" in title:
                    # 台風番号抽出
                    num_match = re.search(r"台風\s*([0-9０-９]+)\s*号", title)
                    if num_match:
                        typhoon_no = num_match.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789"))
                        if "発生" in title:
                            await self._send_to_info(f"【台風情報】台風{typhoon_no}号が発生しました")
                            self.sent_ids.add(id_)
                            await self._exec_log()
                        elif "熱帯低気圧" in title:
                            await self._send_to_info(f"【台風情報】台風{typhoon_no}号は熱帯低気圧になりました")
                            self.sent_ids.add(id_)
                            await self._exec_log()


        except Exception as e:
            await self._log(f"[JMA] フィード処理例外: {e}")

    async def _send_to_info(self, message):
        for ch_id in TARGET_CHANNEL_IDS:
            try:
                ch = self.bot.get_channel(ch_id) or await self.bot.fetch_channel(ch_id)
                if ch:
                    await ch.send(message)
            except Exception as e:
                await self._log(f"[JMA] 送信失敗 {ch_id}: {e}")

    def _pref_from_text(self, text):
        if not text:
            return None
        for p in PREF_LIST:
            if p in text:
                return p
        return None

async def setup(bot):
    await bot.add_cog(DisasterWeather(bot))
