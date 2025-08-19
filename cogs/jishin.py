import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_ROLE_IDS = [1257973629652570154, 1008232882755620946]  # 許可するロールID
LOG_CHANNEL_ID = 1404648254452400179  # 実行ログチャンネルID

# ----- ロールチェック（モジュールレベル関数） -----
def role_check(interaction: discord.Interaction) -> bool:
    return any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)


TARGET_CHANNEL_IDS = [
    1400485670321000510,  # サーバーB
    1367045548653416518   # サーバーC
]

TEMPLATE_CHOICES = {
    "国内地震情報": "＠国内地震情報＠",
    "海外地震情報": "＊海外地震情報＊"
}


class JishinCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="jishin", description="地震情報を送信（選択式）")
    @app_commands.check(role_check)  # ← モジュールレベルの関数を渡す
    @app_commands.describe(
        template="冒頭テンプレート",
        time="発生時刻 (例: 18:57)",
        epicenter="震源（例: 長野県中部）",
        magnitude="マグニチュード（例: 7.0）",
        depth="深さ（例: 10km, ごく浅いなど）",
        shindo="震度",
        tsunami="津波情報"
    )
    @app_commands.choices(
        template=[app_commands.Choice(name=k, value=v) for k, v in TEMPLATE_CHOICES.items()],
        shindo=[app_commands.Choice(name=s, value=s) for s in [
            "１", "２", "３", "４", "５弱", "５強", "６弱", "６強", "７", "不明"
        ]],
        tsunami=[app_commands.Choice(name=s, value=s) for s in [
            "無し",
            "若干の海面変動あり",
            "津波注意報発表中",
            "津波警報発表中",
            "大津波警報発表中",
            "近傍で発生するも日本には被害なし"
        ]]
    )
    async def jishin(
        self,
        interaction: discord.Interaction,
        template: app_commands.Choice[str],
        time: str,
        epicenter: str,
        magnitude: str,
        depth: str,
        shindo: app_commands.Choice[str],
        tsunami: app_commands.Choice[str]
    ):
        message = (
            f"{template.value}\n"
            f"発生時刻：{time}\n"
            f"震源：{epicenter}\n"
            f"マグニチュード：{magnitude}\n"
            f"深さ：{depth}\n"
            f"震度：{shindo.value}\n"
            f"津波：{tsunami.value}"
        )

        success = 0
        for channel_id in TARGET_CHANNEL_IDS:
            ch = self.bot.get_channel(channel_id)
            if ch:
                try:
                    await ch.send(message)
                    success += 1
                except Exception as e:
                    print(f"❌ Failed to send to {channel_id}: {e}")

        # 実行者ログ（メンションなし、ユーザーIDのみ）
        log_ch = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_ch:
            try:
                await log_ch.send(f"jishinコマンド実行者: `{interaction.user.id}`")
            except Exception as e:
                print(f"❌ Failed to log command: {e}")

        await interaction.response.send_message(f"✅ {success} チャンネルに送信しました。", ephemeral=True)

    @jishin.error
    async def jishin_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(JishinCommand(bot))
