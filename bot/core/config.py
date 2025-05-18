import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the utils module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from bot.utils.secure_logging import get_secure_logger

# Create a secure logger
secure_logger = get_secure_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Discord bot token
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    secure_logger.error("DISCORD_TOKEN not found in .env file!")
    print("ERROR: DISCORD_TOKEN not found in .env file!")
    print("Please add your Discord bot token to the .env file.")
    print("See .env.example for required variables.")

# Default guild ID for guild-specific commands
DEFAULT_GUILD_ID = os.environ.get('DEFAULT_GUILD_ID')
if DEFAULT_GUILD_ID:
    try:
        DEFAULT_GUILD_ID = int(DEFAULT_GUILD_ID)
    except ValueError:
        secure_logger.warning("DEFAULT_GUILD_ID must be an integer. Using None instead.")
        print("WARNING: DEFAULT_GUILD_ID must be an integer. Using None instead.")
        DEFAULT_GUILD_ID = None

# Bot configuration
BOT_PREFIX = os.environ.get('BOT_PREFIX', '!')

# OpenRouter API key for AI chat
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    secure_logger.warning("OPENROUTER_API_KEY not found in .env file. AI chat functionality will be disabled.")

# YouTube API key
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    secure_logger.warning("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not found in .env file. Spotify functionality will be disabled.")

# Tenor API key for GIF search
TENOR_API_KEY = os.environ.get('TENOR_API_KEY')
if not TENOR_API_KEY:
    secure_logger.warning("TENOR_API_KEY not found in .env file. GIF search functionality will be disabled.")

# OpenWeatherMap API key for weather forecasts
OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
if not OPENWEATHERMAP_API_KEY:
    secure_logger.warning("OPENWEATHERMAP_API_KEY not found in .env file. Weather functionality will be disabled.")

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
