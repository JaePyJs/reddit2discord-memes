import os
from dotenv import load_dotenv
import sys

# Import secure logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from bot.utils.secure_logging import get_secure_logger

# Create a secure logger
secure_logger = get_secure_logger(__name__)

# Load environment variables
load_dotenv()

# Load token from environment variables for security
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# If token is not found, provide a helpful error message
if not DISCORD_TOKEN:
    secure_logger.error("DISCORD_TOKEN not found in .env file!")
    print("ERROR: DISCORD_TOKEN not found in .env file!")
    print("Please add your Discord bot token to the .env file.")
    print("See .env.example for required variables.")

# Bot configuration
BOT_PREFIX = os.environ.get('BOT_PREFIX', '!')

# OpenRouter API key for AI chat
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    secure_logger.warning("OPENROUTER_API_KEY not found in .env file. AI chat functionality will be disabled.")

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
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    secure_logger.warning("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not found in .env file. Spotify functionality will be disabled.")

# API keys for new integrations
TENOR_API_KEY = os.environ.get('TENOR_API_KEY')
if not TENOR_API_KEY:
    secure_logger.warning("TENOR_API_KEY not found in .env file. GIF search functionality will be disabled.")

OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY')
if not OPENWEATHERMAP_API_KEY:
    secure_logger.warning("OPENWEATHERMAP_API_KEY not found in .env file. Weather functionality will be disabled.")

# Default guild ID (can be None for global commands)
DEFAULT_GUILD_ID = os.environ.get('DEFAULT_GUILD_ID', None)
if DEFAULT_GUILD_ID:
    try:
        DEFAULT_GUILD_ID = int(DEFAULT_GUILD_ID)
    except ValueError:
        secure_logger.warning("DEFAULT_GUILD_ID must be an integer. Using None instead.")
        print("WARNING: DEFAULT_GUILD_ID must be an integer. Using None instead.")
        DEFAULT_GUILD_ID = None
