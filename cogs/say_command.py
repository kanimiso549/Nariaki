import discord
from discord import app_commands
from discord.ext import commands

ALLOWED_ROLE_IDS = "1084660531559944302"

def role_check(interaction: discord.Interaction):
    return any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)

class SayCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="匿名でBotが指定されたメッセージを送信します")
    @app_commands.describe(message="送信したいメッセージ")
    async def say(self, interaction: discord.Interaction, message: str):
        # 応答は実行者のみ（匿名）
        await interaction.response.send_message("✅ 匿名メッセージを送信しました。", ephemeral=True)
        await interaction.channel.send(message)

        # ログ
        log_channel = self.bot.get_channel(self.bot.log_channel_id)
        if log_channel:
            embed = discord.Embed(title="📢 匿名メッセージ実行ログ", color=discord.Color.orange())
            embed.add_field(name="ユーザー", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
            embed.add_field(name="送信チャンネル", value=f"<#{interaction.channel.id}>", inline=True)
            embed.add_field(name="メッセージ", value=message[:1000] or "(空)", inline=False)
            embed.set_footer(text=f"ユーザーID: {interaction.user.id} • サーバーID: {interaction.guild.id}")
            await log_channel.send(embed=embed)
    @say.error
    async def manual_send_error(interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)


async def setup(bot):
    await bot.add_cog(SayCommand(bot))
