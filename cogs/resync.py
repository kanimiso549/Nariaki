import discord
from discord import app_commands
from discord.ext import commands

class ResyncCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="resynccommands", description="スラッシュコマンドを再同期します（管理者専用）")
    async def resync_commands(self, interaction: discord.Interaction):
        # 実行者が管理者かどうか確認
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 このコマンドは管理者専用です。", ephemeral=True)
            return

        try:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(f"✅ {len(synced)} 件のコマンドを再同期しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ 再同期中にエラーが発生しました: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ResyncCommands(bot))
