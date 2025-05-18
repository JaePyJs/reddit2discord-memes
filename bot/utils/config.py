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

# Bot configuration
BOT_PREFIX = os.environ.get('BOT_PREFIX', '!')

# OpenRouter API key for AI chat
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')

# Directory paths
TEMPLATE_DIR = 'templates'
SAVED_MEMES_DIR = 'saved_memes'
ASSETS_DIR = 'assets'
LOGS_DIR = 'logs'
DB_PATH = 'meme_bot.db'

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'discord_meme_bot')
# Enable/disable MongoDB (use SQLite for everything if False)
USE_MONGO_FOR_AI = os.environ.get('USE_MONGO_FOR_AI', 'True').lower() in ('true', '1', 't')

# Music bot configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '6e5f99ad261f4a249e062b1743de5217')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '78d7e0ef160d47e4af1235bc4b07d101')

# Default guild ID (can be None for global commands)
DEFAULT_GUILD_ID = os.environ.get('DEFAULT_GUILD_ID', None)
if DEFAULT_GUILD_ID:
    try:
        DEFAULT_GUILD_ID = int(DEFAULT_GUILD_ID)
    except ValueError:
        print("WARNING: DEFAULT_GUILD_ID must be an integer. Using None instead.")
        DEFAULT_GUILD_ID = None
