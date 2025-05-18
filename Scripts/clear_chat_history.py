"""
Script to clear chat history from the MongoDB database.

This script provides options to:
1. Clear all chat history
2. Clear only mention-based chat history
3. Clear chat history for specific channels or users

Usage:
    python Scripts/clear_chat_history.py --all
    python Scripts/clear_chat_history.py --mentions
    python Scripts/clear_chat_history.py --channel <channel_id>
    python Scripts/clear_chat_history.py --user <user_id>
"""

import os
import sys
import argparse
import asyncio
import motor.motor_asyncio
from pymongo.errors import PyMongoError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import MongoDB configuration or use defaults
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bot.core.config import MONGO_URI, MONGO_DB_NAME
except ImportError:
    # Default MongoDB connection settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "discord_meme_bot")
    logger.warning(f"Using default MongoDB settings: {MONGO_URI}, {MONGO_DB_NAME}")

async def clear_all_chat_history():
    """Clear all chat history from the database."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get collections
        conversations = db["ai_conversations"]
        messages = db["ai_messages"]
        
        # Delete all messages
        messages_result = await messages.delete_many({})
        logger.info(f"Deleted {messages_result.deleted_count} messages")
        
        # Mark all conversations as archived
        conversations_result = await conversations.update_many(
            {},
            {"$set": {"is_archived": True}}
        )
        logger.info(f"Archived {conversations_result.modified_count} conversations")
        
        return True
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return False

async def clear_mention_chat_history():
    """Clear only mention-based chat history."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get collections
        conversations = db["ai_conversations"]
        messages = db["ai_messages"]
        
        # Find mention-based conversations (channel_id starts with "mention_")
        mention_conversations = await conversations.find(
            {"channel_id": {"$regex": "^mention_"}}
        ).to_list(length=None)
        
        if not mention_conversations:
            logger.info("No mention-based conversations found")
            return True
        
        # Get conversation IDs
        conversation_ids = [str(conv["_id"]) for conv in mention_conversations]
        
        # Delete messages for these conversations
        messages_result = await messages.delete_many(
            {"conversation_id": {"$in": conversation_ids}}
        )
        logger.info(f"Deleted {messages_result.deleted_count} mention-based messages")
        
        # Mark conversations as archived
        conversations_result = await conversations.update_many(
            {"_id": {"$in": conversation_ids}},
            {"$set": {"is_archived": True}}
        )
        logger.info(f"Archived {conversations_result.modified_count} mention-based conversations")
        
        return True
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return False

async def clear_channel_chat_history(channel_id):
    """Clear chat history for a specific channel."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get collections
        conversations = db["ai_conversations"]
        messages = db["ai_messages"]
        
        # Find conversations for this channel
        channel_conversations = await conversations.find(
            {"channel_id": str(channel_id)}
        ).to_list(length=None)
        
        if not channel_conversations:
            logger.info(f"No conversations found for channel {channel_id}")
            return True
        
        # Get conversation IDs
        conversation_ids = [str(conv["_id"]) for conv in channel_conversations]
        
        # Delete messages for these conversations
        messages_result = await messages.delete_many(
            {"conversation_id": {"$in": conversation_ids}}
        )
        logger.info(f"Deleted {messages_result.deleted_count} messages for channel {channel_id}")
        
        # Mark conversations as archived
        conversations_result = await conversations.update_many(
            {"_id": {"$in": conversation_ids}},
            {"$set": {"is_archived": True}}
        )
        logger.info(f"Archived {conversations_result.modified_count} conversations for channel {channel_id}")
        
        return True
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return False

async def clear_user_chat_history(user_id):
    """Clear chat history for a specific user."""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get collections
        conversations = db["ai_conversations"]
        messages = db["ai_messages"]
        
        # Find conversations for this user (including DMs and mentions)
        user_conversations = await conversations.find(
            {"$or": [
                {"user_id": str(user_id)},
                {"channel_id": f"dm_{user_id}"},
                {"channel_id": {"$regex": f"mention_.*_{user_id}"}}
            ]}
        ).to_list(length=None)
        
        if not user_conversations:
            logger.info(f"No conversations found for user {user_id}")
            return True
        
        # Get conversation IDs
        conversation_ids = [str(conv["_id"]) for conv in user_conversations]
        
        # Delete messages for these conversations
        messages_result = await messages.delete_many(
            {"conversation_id": {"$in": conversation_ids}}
        )
        logger.info(f"Deleted {messages_result.deleted_count} messages for user {user_id}")
        
        # Mark conversations as archived
        conversations_result = await conversations.update_many(
            {"_id": {"$in": conversation_ids}},
            {"$set": {"is_archived": True}}
        )
        logger.info(f"Archived {conversations_result.modified_count} conversations for user {user_id}")
        
        # Also delete messages where this user was the sender
        user_messages_result = await messages.delete_many(
            {"user_id": str(user_id)}
        )
        logger.info(f"Deleted {user_messages_result.deleted_count} additional messages sent by user {user_id}")
        
        return True
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        return False

async def main():
    """Main function to parse arguments and call appropriate functions."""
    parser = argparse.ArgumentParser(description="Clear chat history from MongoDB")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Clear all chat history")
    group.add_argument("--mentions", action="store_true", help="Clear only mention-based chat history")
    group.add_argument("--channel", type=str, help="Clear chat history for a specific channel")
    group.add_argument("--user", type=str, help="Clear chat history for a specific user")
    
    args = parser.parse_args()
    
    if args.all:
        logger.info("Clearing all chat history...")
        success = await clear_all_chat_history()
    elif args.mentions:
        logger.info("Clearing mention-based chat history...")
        success = await clear_mention_chat_history()
    elif args.channel:
        logger.info(f"Clearing chat history for channel {args.channel}...")
        success = await clear_channel_chat_history(args.channel)
    elif args.user:
        logger.info(f"Clearing chat history for user {args.user}...")
        success = await clear_user_chat_history(args.user)
    
    if success:
        logger.info("Chat history cleared successfully")
    else:
        logger.error("Failed to clear chat history")

if __name__ == "__main__":
    asyncio.run(main())
