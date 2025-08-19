import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_ROLE_IDS = [1257973629652570154, 1008232882755620946]

class MyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_check(interaction: discord.Interaction) -> bool:
        """スラッシュコマンド実行者が許可されたロールを持っているか確認"""
        return any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)

    @app_commands.command(name="send_alert", description="テスト用の送信コマンド")
    @app_commands.check(role_check)
    async def send_alert(self, interaction: discord.Interaction):
        await interaction.response.send_message("許可されたロールを持っているので実行できます！")

    @send_alert.error
    async def send_alert_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MyCommands(bot))
