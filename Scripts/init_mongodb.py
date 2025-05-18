"""
MongoDB initialization script for the Discord bot.
Run this script to set up the MongoDB database and collections.
"""

import asyncio
import logging
from bot.utils import mongo_db
from bot.utils.config import MONGO_URI, MONGO_DB_NAME, USE_MONGO_FOR_AI

async def init_mongo():
    """Initialize MongoDB database and collections."""
    print(f"Initializing MongoDB at {MONGO_URI}")
    print(f"Database: {MONGO_DB_NAME}")
    
    # Initialize connections and create indexes
    success = await mongo_db.initialize_mongodb()
    
    if success:
        print("MongoDB initialization successful!")
        print("Created collections:")
        print("- ai_channels: Stores which channel in each guild is set for AI chat")
        print("- ai_conversations: Stores conversation metadata")
        print("- ai_messages: Stores the actual messages in conversations")
        print("- ai_user_preferences: Stores user preferences for AI chat")
    else:
        print("MongoDB initialization failed. Check your connection settings.")
        print("The bot will use in-memory storage as a fallback.")

if __name__ == "__main__":
    # Check if MongoDB is enabled
    if not USE_MONGO_FOR_AI:
        print("MongoDB is disabled in config. Set USE_MONGO_FOR_AI=True to enable it.")
        print("Skipping initialization.")
        exit(0)
    
    # Run initialization
    asyncio.run(init_mongo())
