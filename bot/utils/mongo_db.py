"""
MongoDB utilities for Discord bot AI chat functionality.
This module provides MongoDB integration for storing and retrieving AI chat data.
"""

import os
import logging
import datetime
import motor.motor_asyncio
from pymongo.errors import PyMongoError
from typing import Dict, List, Optional, Any, Union

# Import DB configuration or set defaults
try:
    from bot.utils.config import MONGO_URI, MONGO_DB_NAME
except ImportError:
    # Default MongoDB connection settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "discord_meme_bot")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize async MongoDB client
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    # Collections
    ai_channels = db["ai_channels"]
    ai_conversations = db["ai_conversations"]
    ai_messages = db["ai_messages"]
    ai_user_preferences = db["ai_user_preferences"]
    logger.info(f"Connected to MongoDB: {MONGO_DB_NAME}")
except PyMongoError as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    # Fallback to not crash the app if MongoDB is not available
    client = None
    db = None
    ai_channels = None
    ai_conversations = None
    ai_messages = None
    ai_user_preferences = None

# Create indexes for better query performance
async def create_indexes():
    """Create necessary indexes for MongoDB collections."""
    if db is None:
        logger.warning("MongoDB not available. Skipping index creation.")
        return
    
    try:
        # User ID index
        await ai_user_preferences.create_index("user_id", unique=True)
        
        # Channel indexes
        await ai_channels.create_index("guild_id", unique=True)
        
        # Conversation indexes
        await ai_conversations.create_index("channel_id")
        await ai_conversations.create_index("user_id")
        await ai_conversations.create_index("last_activity")
        
        # Message indexes
        await ai_messages.create_index("conversation_id")
        await ai_messages.create_index([("conversation_id", 1), ("timestamp", 1)])
        
        logger.info("MongoDB indexes created successfully.")
    except PyMongoError as e:
        logger.error(f"Failed to create MongoDB indexes: {e}")

# AI Channels functions
async def set_ai_channel(guild_id: int, channel_id: int, user_id: Optional[int] = None) -> bool:
    """
    Set or update the AI chat channel for a guild.
    
    Args:
        guild_id: Discord guild ID
        channel_id: Discord channel ID
        user_id: (Optional) User ID who set the channel
        
    Returns:
        True if successful, False otherwise
    """
    if ai_channels is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return False
    
    try:
        result = await ai_channels.update_one(
            {"guild_id": str(guild_id)},
            {
                "$set": {
                    "channel_id": str(channel_id),
                    "set_by_user_id": str(user_id) if user_id else None,
                    "updated_at": datetime.datetime.now()
                }
            },
            upsert=True
        )
        return result.acknowledged
    except PyMongoError as e:
        logger.error(f"MongoDB error in set_ai_channel: {e}")
        return False

async def get_ai_channel(guild_id: int) -> Optional[int]:
    """
    Get the AI chat channel ID for a guild.
    
    Args:
        guild_id: Discord guild ID
        
    Returns:
        Channel ID if found, None otherwise
    """
    if ai_channels is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return None
    
    try:
        result = await ai_channels.find_one({"guild_id": str(guild_id)})
        return int(result["channel_id"]) if result else None
    except PyMongoError as e:
        logger.error(f"MongoDB error in get_ai_channel: {e}")
        return None

async def is_ai_channel(guild_id: int, channel_id: int) -> bool:
    """
    Check if a channel is the designated AI chat channel for a guild.
    
    Args:
        guild_id: Discord guild ID
        channel_id: Discord channel ID to check
        
    Returns:
        True if this is the active AI chat channel
    """
    if ai_channels is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return False
    
    try:
        result = await ai_channels.find_one({
            "guild_id": str(guild_id),
            "channel_id": str(channel_id)
        })
        return bool(result)
    except PyMongoError as e:
        logger.error(f"MongoDB error in is_ai_channel: {e}")
        return False

# AI Conversation management
async def create_conversation(
    channel_id: str, 
    guild_id: Optional[str] = None, 
    user_id: Optional[str] = None, 
    is_dm: bool = False
) -> Optional[str]:
    """
    Create a new conversation and return its ID.
    
    Args:
        channel_id: Discord channel ID
        guild_id: Discord guild ID (None for DMs)
        user_id: User ID who started the conversation (required for DMs)
        is_dm: Whether this is a DM conversation
        
    Returns:
        Conversation ID if created successfully, None otherwise
    """
    if ai_conversations is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return None
    
    try:
        # Validate parameters for DM conversations
        if is_dm and not user_id:
            logger.error("User ID is required for DM conversations")
            return None
        
        # Create conversation document
        conversation = {
            "channel_id": str(channel_id),
            "guild_id": str(guild_id) if guild_id else None,
            "user_id": str(user_id) if user_id else None,
            "is_dm": is_dm,
            "start_time": datetime.datetime.now(),
            "last_activity": datetime.datetime.now(),
            "is_archived": False
        }
        
        result = await ai_conversations.insert_one(conversation)
        return str(result.inserted_id) if result.acknowledged else None
    except PyMongoError as e:
        logger.error(f"MongoDB error in create_conversation: {e}")
        return None

async def get_or_create_conversation(
    channel_id: str, 
    guild_id: Optional[str] = None, 
    user_id: Optional[str] = None, 
    is_dm: bool = False
) -> Optional[str]:
    """
    Get an existing active conversation or create a new one.
    
    Args:
        channel_id: Discord channel ID or DM channel identifier
        guild_id: Discord guild ID (None for DMs)
        user_id: User ID (required for DMs)
        is_dm: Whether this is a DM conversation
        
    Returns:
        Conversation ID
    """
    if ai_conversations is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return None
    
    try:
        # Form the query based on whether it's a DM or guild channel
        query = {
            "is_archived": False,
            "is_dm": is_dm
        }
        
        if is_dm:
            if not user_id:
                logger.error("User ID is required for DM conversations")
                return None
            query["user_id"] = str(user_id)
        else:
            query["channel_id"] = str(channel_id)
            if guild_id:
                query["guild_id"] = str(guild_id)
        
        # Find an existing conversation
        conversation = await ai_conversations.find_one(
            query,
            sort=[("last_activity", -1)]  # Get the most recent conversation
        )
        
        if conversation:
            # Update last activity
            await ai_conversations.update_one(
                {"_id": conversation["_id"]},
                {"$set": {"last_activity": datetime.datetime.now()}}
            )
            return str(conversation["_id"])
        
        # No existing conversation found, create a new one
        return await create_conversation(channel_id, guild_id, user_id, is_dm)
    except PyMongoError as e:
        logger.error(f"MongoDB error in get_or_create_conversation: {e}")
        return None

async def add_message(
    conversation_id: str,
    role: str,
    content: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None
) -> Optional[str]:
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: Conversation ID
        role: Message role ('user' or 'assistant')
        content: Message content
        user_id: Discord user ID (for user messages)
        username: Discord username (for user messages)
        
    Returns:
        Message ID if added successfully, None otherwise
    """
    if ai_messages is None or ai_conversations is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return None
    
    try:
        # Create message document
        message = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "user_id": str(user_id) if user_id else None,
            "username": username,
            "timestamp": datetime.datetime.now()
        }
        
        # Insert message
        result = await ai_messages.insert_one(message)
        
        # Update conversation's last activity
        await ai_conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"last_activity": datetime.datetime.now()}}
        )
        
        return str(result.inserted_id) if result.acknowledged else None
    except PyMongoError as e:
        logger.error(f"MongoDB error in add_message: {e}")
        return None

async def get_conversation_messages(
    conversation_id: str, 
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get messages for a conversation.
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of message documents
    """
    if ai_messages is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return []
    
    try:
        cursor = ai_messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).limit(limit)
        
        return await cursor.to_list(length=limit)
    except PyMongoError as e:
        logger.error(f"MongoDB error in get_conversation_messages: {e}")
        return []

async def clear_conversation_history(
    conversation_id: str, 
    count: Optional[int] = None
) -> bool:
    """
    Clear history for a conversation.
    
    Args:
        conversation_id: Conversation ID
        count: Number of most recent messages to clear (None means all)
        
    Returns:
        True if history was cleared successfully
    """
    if ai_messages is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return False
    
    try:
        if count is None:
            # Delete all messages
            result = await ai_messages.delete_many({"conversation_id": conversation_id})
            return result.acknowledged
        else:
            # Get message IDs sorted by timestamp (newest first)
            cursor = ai_messages.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", -1).limit(count)
            
            messages = await cursor.to_list(length=count)
            if not messages:
                return False
                
            # Extract message IDs
            message_ids = [msg["_id"] for msg in messages]
            
            # Delete specific messages
            result = await ai_messages.delete_many({"_id": {"$in": message_ids}})
            return result.acknowledged
    except PyMongoError as e:
        logger.error(f"MongoDB error in clear_conversation_history: {e}")
        return False

async def archive_conversation(conversation_id: str) -> bool:
    """
    Archive a conversation.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        True if archived successfully
    """
    if ai_conversations is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return False
    
    try:
        result = await ai_conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"is_archived": True, "archived_at": datetime.datetime.now()}}
        )
        return result.acknowledged
    except PyMongoError as e:
        logger.error(f"MongoDB error in archive_conversation: {e}")
        return False

# User preferences
async def set_user_preferences(
    user_id: str,
    preferences: Dict[str, Any]
) -> bool:
    """
    Set user preferences for AI chat.
    
    Args:
        user_id: Discord user ID
        preferences: Dictionary of preferences
        
    Returns:
        True if set successfully
    """
    if ai_user_preferences is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return False
    
    try:
        # Add timestamps
        preferences["updated_at"] = datetime.datetime.now()
        
        result = await ai_user_preferences.update_one(
            {"user_id": str(user_id)},
            {
                "$set": preferences,
                "$setOnInsert": {"created_at": datetime.datetime.now()}
            },
            upsert=True
        )
        return result.acknowledged
    except PyMongoError as e:
        logger.error(f"MongoDB error in set_user_preferences: {e}")
        return False

async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user preferences for AI chat.
    
    Args:
        user_id: Discord user ID
        
    Returns:
        Dictionary of preferences or default preferences
    """
    if ai_user_preferences is None:
        logger.warning("MongoDB not available. Using in-memory storage.")
        return get_default_preferences()
    
    try:
        result = await ai_user_preferences.find_one({"user_id": str(user_id)})
        return result if result else get_default_preferences()
    except PyMongoError as e:
        logger.error(f"MongoDB error in get_user_preferences: {e}")
        return get_default_preferences()

def get_default_preferences() -> Dict[str, Any]:
    """Get default user preferences."""
    return {
        "tone_preference": "super_casual",
        "mention_name": True,
        "emoji_level": 3
    }

# Utility functions for fallback/in-memory operations
fallback_active_channels = {}
fallback_message_history = {}

async def fallback_set_ai_channel(guild_id: int, channel_id: int) -> bool:
    """
    Set the active AI chat channel for a guild using in-memory fallback.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID where the AI should respond
    """
    fallback_active_channels[guild_id] = channel_id
    return True

async def fallback_is_ai_channel(guild_id: int, channel_id: int) -> bool:
    """
    Check if the channel is the designated AI chat channel for the guild using in-memory fallback.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID to check
    """
    return fallback_active_channels.get(guild_id) == channel_id

async def fallback_get_ai_channel(guild_id: int) -> Optional[int]:
    """
    Get the active AI chat channel ID for a guild using in-memory fallback.
    
    Args:
        guild_id: The Discord guild ID
    """
    return fallback_active_channels.get(guild_id)

# Initialization function to be called when the bot starts
async def initialize_mongodb():
    """Initialize MongoDB connections and indexes."""
    if db is not None:
        await create_indexes()
        return True
    else:
        logger.warning("MongoDB not available. Using in-memory fallback.")
        return False
