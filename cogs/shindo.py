import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_ROLE_IDS = [1257973629652570154, 1008232882755620946]

def role_check(interaction: discord.Interaction):
    return any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)

TARGET_CHANNEL_IDS = [
    1400485670321000510,
    1367045548653416518
]

SHINDO_CHOICES = [
    app_commands.Choice(name="3", value="3"),
    app_commands.Choice(name="4", value="4"),
    app_commands.Choice(name="5弱", value="5弱"),
    app_commands.Choice(name="5強", value="5強"),
    app_commands.Choice(name="6弱", value="6弱"),
    app_commands.Choice(name="6強", value="6強"),
    app_commands.Choice(name="7", value="7"),
]

class ShindoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shindo", description="震度速報を送信します")
    @app_commands.describe(shindo="観測された震度を選んでください")
    @app_commands.choices(shindo=SHINDO_CHOICES)
    async def shindo(self, interaction: discord.Interaction, shindo: app_commands.Choice[str]):
        message = f"＊震度速報＊\n震度{shindo.value}を観測しました"

        success = 0
        for channel_id in TARGET_CHANNEL_IDS:
            channel = interaction.client.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(message)
                    success += 1
                except Exception as e:
                    print(f"❌ Failed to send to {channel_id}: {e}")

        await interaction.response.send_message(f"✅ {success} チャンネルに送信しました。", ephemeral=True)

    @shindo.error
    async def manual_send_error(interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShindoCommand(bot))
