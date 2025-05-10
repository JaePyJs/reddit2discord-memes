import os
from dotenv import load_dotenv

load_dotenv()

# Load token from environment variables for security
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# If token is not found, provide a helpful error message
if not DISCORD_TOKEN:
    print("ERROR: DISCORD_TOKEN not found in .env file!")
    print("Please add your Discord bot token to the .env file:")
    print("DISCORD_TOKEN=your_token_here")
TEMPLATE_DIR = 'templates'
SAVED_MEMES_DIR = 'saved_memes'
ASSETS_DIR = 'assets'
LOGS_DIR = 'logs'
DB_PATH = 'meme_bot.db'
