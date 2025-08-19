import discord
from discord.ext import commands

class Yoroshii(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # スラッシュコマンド
    @discord.app_commands.command(name="name", description="えーっと…わたしのむねにおｔ")
    async def yoroshii_command(self, interaction: discord.Interaction):
        nickname = interaction.user.nick if interaction.user.nick else interaction.user.name
        mention = interaction.user.mention
        await interaction.response.send_message(f"えーっと…{nickname}さんでよろしいですか？")

async def setup(bot: commands.Bot):
    await bot.add_cog(Yoroshii(bot))
