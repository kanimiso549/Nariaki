import discord
from discord.ext import commands, tasks
import random
import datetime
import jpholiday

class ScheduledSender(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_weekday = 6  # 日曜日 = 6
        self.target_hour = 19    # JST
        self.target_minute = 0
        self.source_channel_id = 1401194781560016907
        self.destination_channel_ids = [
            1400485670321000510,
            1367045548653416518,
        ]
        self.check_time.start()

    def cog_unload(self):
        self.check_time.cancel()

    @tasks.loop(minutes=1)
    async def check_time(self):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)  # JSTに変換
        if (now.weekday() == self.target_weekday and
            now.hour == self.target_hour and
            now.minute == self.target_minute):
            
            # 翌日の日付（JST）
            tomorrow = now + datetime.timedelta(days=1)

            # 翌日が祝日ならスキップ
            if jpholiday.is_holiday(tomorrow.date()):
                print("🚫 翌日が祝日のため送信をスキップしました。")
                return
            
            await self.send_random_file()

    async def send_random_file(self):
        source_channel = self.bot.get_channel(self.source_channel_id)
        if not source_channel:
            print("❌ ソースチャンネルが見つかりません。")
            return

        files = []
        async for msg in source_channel.history(limit=100):
            files.extend(msg.attachments)

        if not files:
            print("⚠️ 添付ファイルが見つかりません。")
            return

        chosen_file = random.choice(files)

        for channel_id in self.destination_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(file=await chosen_file.to_file())
                print(f"✅ ファイル送信完了 → {channel.name}")
            else:
                print(f"⚠️ チャンネルが見つかりません → {channel_id}")

async def setup(bot):
    await bot.add_cog(ScheduledSender(bot))
