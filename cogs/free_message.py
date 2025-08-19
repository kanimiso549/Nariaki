import discord
from discord import app_commands
from discord.ext import commands

TARGET_CHANNEL_IDS = [
    1400485670321000510,
    1367045548653416518
]

LOG_USER_ID_CHANNEL = 1404648254452400179  # 実行者ID送信用

MESSAGE_DEFINITIONS = {
    "forecast": "**緊急地震速報(予報/念の為海岸から離れて)**",
    "warning": "**緊急地震速報(警報/海岸から離れて)**",
    "tokubetsu": "**特別警報**",
    "hosoku": "＊補足情報＊",
    "usgs": "＊海外地震情報(USGS/更新)＊",
    "kishocho": "＊海外地震情報(気象庁)＊",
    "choshuki": "＊長周期地震動に関する観測情報＊",
    "oshirase": "＊お知らせ＊",
    "news": "＊最新ニュース＊",
    "kisho": "＊気象情報＊",
    "rever": "＊河川情報＊"
}


# ----- 管理者チェック（モジュールレベル関数） -----
def admin_only_check(interaction: discord.Interaction) -> bool:
    """サーバー管理者権限を持っているか確認"""
    return bool(interaction.user.guild_permissions.administrator)


class FreeMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="free_message", description="テンプレと自由文で送信")
    @app_commands.check(admin_only_check)  # ← クラス外関数を渡す
    @app_commands.describe(
        kind="送信するメッセージ種類を選択",
        line1="1行目のテキスト（任意）",
        line2="2行目のテキスト（任意）",
        line3="3行目のテキスト（任意）"
    )
    @app_commands.choices(
        kind=[
            app_commands.Choice(name="緊急地震速報（予報）", value="forecast"),
            app_commands.Choice(name="緊急地震速報（警報）", value="warning"),
            app_commands.Choice(name="特別警報", value="tokubetsu"),
            app_commands.Choice(name="補足情報", value="hosoku"),
            app_commands.Choice(name="海外地震情報（USGS）", value="usgs"),
            app_commands.Choice(name="海外地震情報（気象庁）", value="kishocho"),
            app_commands.Choice(name="長周期地震動", value="choshuki"),
            app_commands.Choice(name="お知らせ", value="oshirase"),
            app_commands.Choice(name="最新ニュース", value="news"),
            app_commands.Choice(name="気象情報", value="kisho"),
            app_commands.Choice(name="河川情報", value="rever")
        ]
    )
    async def free_message(
        self,
        interaction: discord.Interaction,
        kind: app_commands.Choice[str],
        line1: str = "",
        line2: str = "",
        line3: str = ""
    ):
        header = MESSAGE_DEFINITIONS.get(kind.value, "")
        additions = "\n".join([s for s in (line1, line2, line3) if s and s.strip()])
        content = f"{header}\n{additions}" if additions else header

        success = 0
        for channel_id in TARGET_CHANNEL_IDS:
            ch = self.bot.get_channel(channel_id)
            if ch:
                try:
                    await ch.send(content)
                    success += 1
                except Exception as e:
                    print(f"❌ Failed to send to {channel_id}: {e}")

        # ログに実行者IDのみ（メンションしない）
        log_ch = self.bot.get_channel(LOG_USER_ID_CHANNEL)
        if log_ch:
            try:
                await log_ch.send(str(interaction.user.id))
            except Exception as e:
                print(f"❌ Failed to send user ID to log channel: {e}")

        await interaction.response.send_message(f"✅ {success} チャンネルに送信しました。", ephemeral=True)

    @free_message.error
    async def free_message_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("このコマンドは管理者のみ実行できます。", ephemeral=True)
        else:
            # 想定外は再送出してトレースを見れるようにする（開発時のみ）
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(FreeMessage(bot))
