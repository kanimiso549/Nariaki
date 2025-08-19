import discord
from discord.ext import commands
from discord import app_commands

SERVER_ROLE_IDS = {
    876782808847220786: {  # サーバーB
        "斉昭用#1": 1390177514747465858,
        "斉昭用#2": 1390177732012277800,
        "斉昭用#3": 1390177846567370772,
        "斉昭用#4": 1390177916515782736,
    },
    1257965388495323208: {  # サーバーC
        "斉昭用#1": 1390181250731479120,
        "斉昭用#2": 1390181474363379762,
        "斉昭用#3": 1390181562720714773,
        "斉昭用#4": 1390181653762281563,
    }
}

TARGET_USER_ID = 1401152015551434802
LOG_CHANNEL_ID = 1328386190231081084

class SwitchRoleButton(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="斉昭用#1", style=discord.ButtonStyle.primary, custom_id="switch_1")
    async def switch_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.switch_role(interaction, "斉昭用#1")

    @discord.ui.button(label="斉昭用#2", style=discord.ButtonStyle.primary, custom_id="switch_2")
    async def switch_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.switch_role(interaction, "斉昭用#2")

    @discord.ui.button(label="斉昭用#3", style=discord.ButtonStyle.primary, custom_id="switch_3")
    async def switch_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.switch_role(interaction, "斉昭用#3")

    @discord.ui.button(label="斉昭用#4", style=discord.ButtonStyle.primary, custom_id="switch_4")
    async def switch_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.switch_role(interaction, "斉昭用#4")

    async def switch_role(self, interaction: discord.Interaction, role_name: str):
        count = 0
        for guild_id, roles in SERVER_ROLE_IDS.items():
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                continue
            try:
                target_member = await guild.fetch_member(TARGET_USER_ID)
            except discord.NotFound:
                continue

            role_ids = list(roles.values())
            role_to_add = guild.get_role(roles[role_name])
            if role_to_add is None:
                continue

            remove_roles = [r for r in target_member.roles if r.id in role_ids and r != role_to_add]
            add_role = role_to_add if role_to_add not in target_member.roles else None

            if remove_roles:
                await target_member.remove_roles(*remove_roles, reason="排他ロール切替")
            if add_role:
                await target_member.add_roles(add_role, reason="選択ロール追加")

            count += 1

        await interaction.response.send_message(
            f"{role_name} に切替を {count} サーバーで実行しました（対象: <@{TARGET_USER_ID}>）。",
            ephemeral=True
        )

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"[通知] 実行者: {interaction.user.mention} により {role_name} が {count} サーバーで適用されました（対象: <@{TARGET_USER_ID}>）"
            )

class SwitchRoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(SwitchRoleButton(self.bot))

    @app_commands.command(name="switch_role", description="ロール切替ボタンを表示")
    async def switch_role_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("切り替えるロールを選択してください。", view=SwitchRoleButton(self.bot), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SwitchRoleCog(bot))
