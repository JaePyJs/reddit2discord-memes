import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord bot token
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# Default guild ID for guild-specific commands
DEFAULT_GUILD_ID = os.environ.get('DEFAULT_GUILD_ID')

# Bot configuration
BOT_PREFIX = os.environ.get('BOT_PREFIX', '!')

# OpenRouter API key for AI chat
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')

# YouTube API key
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')

# Directory paths
TEMPLATE_DIR = 'templates'
SAVED_MEMES_DIR = 'saved_memes'
ASSETS_DIR = 'assets'
LOGS_DIR = 'logs'
DB_PATH = 'data/meme_bot.db'
CACHE_DIR = 'data/cache'

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'discord_meme_bot')
# Enable/disable MongoDB (use SQLite for everything if False)
USE_MONGO_FOR_AI = os.environ.get('USE_MONGO_FOR_AI', 'True').lower() in ('true', '1', 't')
