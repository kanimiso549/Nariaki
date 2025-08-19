# delete_commands.py
import discord
from discord.ext import commands
import config

intents = discord.Intents.none()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ logged in as {bot.user} - deleting commands...")

    # --- delete guild commands for all guilds the bot is in ---
    for guild in bot.guilds:
        try:
            # fetch guild commands
            cmds = await bot.tree.fetch_commands(guild=guild)
            if cmds:
                for cmd in cmds:
                    await bot.tree.delete_command(cmd.id, guild=guild)
                    print(f"🗑️ Deleted guild command {cmd.name} from {guild.id}")
        except Exception as e:
            print(f"⚠️ Failed clearing guild {guild.id}: {e}")

    # --- delete global commands ---
    try:
        cmds = await bot.tree.fetch_commands()
        if cmds:
            for cmd in cmds:
                await bot.tree.delete_command(cmd.id)
                print(f"🗑️ Deleted global command {cmd.name}")
    except Exception as e:
        print(f"⚠️ Failed clearing global commands: {e}")

    print("✅ deletion finished. closing bot.")
    await bot.close()

bot.run(config.DISCORD_TOKEN)

