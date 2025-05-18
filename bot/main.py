import discord
from discord import app_commands, Intents
from discord.ext import commands
import os
import logging
import asyncio
from bot.core.config import DISCORD_TOKEN, DEFAULT_GUILD_ID, BOT_PREFIX
from bot.core.dependency_checker import verify_dependencies
from bot.core import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Utility logging helpers
def log_command_registration(cmd_name):
    logging.info(f"Registered slash command: {cmd_name}")

# Basic setup
intents = Intents.default()
intents.message_content = True
intents.guilds = True

# Check dependencies
verify_dependencies()

# Initialize database
db.init_db()
db.add_default_templates()
print("Database initialized with default templates")

# Create bot instance
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Simple test command
@bot.tree.command(name='test', description='Test command')
async def test(interaction: discord.Interaction):
    context = "DM" if interaction.guild is None else f"guild {interaction.guild.name}"
    await interaction.response.send_message(f'Test command works! This is a {context}.')

async def load_extensions():
    """Load all extensions (cogs)"""
    # Load all extensions
    extensions = [
        "bot.features.music.commands_setup",
        # "bot.features.memes.commands",  # Temporarily disabled until fully fixed
        "bot.features.reddit.commands",
        "bot.features.ai.commands",
        "bot.features.tenor.commands",
        "bot.features.weather.commands",
        "bot.features.urban.commands"
    ]

    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded {extension} extension")
        except Exception as e:
            print(f"Failed to load {extension}: {e}")
            import traceback
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Load extensions
    await load_extensions()

    try:
        print(f"Syncing commands...")

        # Sync global commands first - this will register all commands globally when DEFAULT_GUILD_ID is empty
        global_commands = await bot.tree.sync()
        print(f'Synced {len(global_commands)} global commands')

        # List all registered commands for debugging
        print("Registered global commands:")
        for cmd in global_commands:
            print(f"- /{cmd.name}: {cmd.description}")

        # Then sync guild commands if specified
        if DEFAULT_GUILD_ID:
            guild = discord.Object(id=DEFAULT_GUILD_ID)
            guild_commands = await bot.tree.sync(guild=guild)
            print(f'Synced {len(guild_commands)} guild commands for guild {DEFAULT_GUILD_ID}')

        print('Bot is ready!')
    except Exception as e:
        print(f"Error syncing commands: {e}")
        import traceback
        traceback.print_exc()

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
