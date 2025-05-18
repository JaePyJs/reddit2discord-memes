"""
MongoDB Integration Tester for AI Chat

This script tests the MongoDB integration for the AI chat functionality.
It allows you to verify that conversations are being stored and retrieved correctly.

Usage:
python test_mongodb.py
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mongodb-tester")

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MongoDB utilities
from bot.utils import mongo_db
from bot.utils.config import MONGO_URI, MONGO_DB_NAME, USE_MONGO_FOR_AI

# Test function to run a full integration test
async def test_mongodb_integration():
    logger.info("Starting MongoDB integration test")
    logger.info(f"MongoDB URI: {MONGO_URI}")
    logger.info(f"Database: {MONGO_DB_NAME}")
    
    if not USE_MONGO_FOR_AI:
        logger.error("MongoDB is not enabled in config. Set USE_MONGO_FOR_AI=True in .env")
        return False
    
    # Step 1: Initialize MongoDB
    await mongo_db.initialize_mongodb()
    
    # Step 2: Test AI channel settings
    test_guild_id = 123456789
    test_channel_id = 987654321
    test_user_id = 111222333
    
    # Set AI channel
    logger.info("Testing set_ai_channel...")
    channel_set = await mongo_db.set_ai_channel(test_guild_id, test_channel_id, test_user_id)
    if not channel_set:
        logger.error("Failed to set AI channel")
        return False
    logger.info("✅ set_ai_channel successful")
    
    # Get AI channel
    ai_channel = await mongo_db.get_ai_channel(test_guild_id)
    if ai_channel != test_channel_id:
        logger.error(f"get_ai_channel returned {ai_channel}, expected {test_channel_id}")
        return False
    logger.info("✅ get_ai_channel successful")
    
    # Check if channel is AI channel
    is_ai = await mongo_db.is_ai_channel(test_guild_id, test_channel_id)
    if not is_ai:
        logger.error("is_ai_channel returned False, expected True")
        return False
    logger.info("✅ is_ai_channel successful")
    
    # Step 3: Test conversation creation and message storage
    logger.info("Testing conversation creation and message handling...")
    
    # Create conversation
    conversation_id = await mongo_db.create_conversation(
        str(test_channel_id),
        str(test_guild_id),
        str(test_user_id),
        False
    )
    
    if not conversation_id:
        logger.error("Failed to create conversation")
        return False
    logger.info(f"✅ create_conversation successful, ID: {conversation_id}")
    
    # Add messages to conversation
    messages = [
        ("user", "Hello, how are you?", test_user_id, "TestUser"),
        ("assistant", "I'm doing well, thank you for asking!"),
        ("user", "What can you do?", test_user_id, "TestUser"),
        ("assistant", "I can help with many tasks, like answering questions and having conversations.")
    ]
    
    for role, content, *args in messages:
        user_id = args[0] if len(args) > 0 and role == "user" else None
        username = args[1] if len(args) > 1 and role == "user" else None
        
        message_id = await mongo_db.add_message(
            conversation_id,
            role,
            content,
            user_id,
            username
        )
        
        if not message_id:
            logger.error(f"Failed to add message: {content}")
            return False
    
    logger.info(f"✅ Added {len(messages)} messages to conversation")
    
    # Retrieve messages
    retrieved_messages = await mongo_db.get_conversation_messages(conversation_id)
    if len(retrieved_messages) != len(messages):
        logger.error(f"Retrieved {len(retrieved_messages)} messages, expected {len(messages)}")
        return False
    
    logger.info(f"✅ Retrieved {len(retrieved_messages)} messages successfully")
    
    # Step 4: Test user preferences
    logger.info("Testing user preferences...")
    
    # Set preferences
    preferences = {
        "tone_preference": "formal",
        "emoji_level": 1,
        "mention_name": False
    }
    
    prefs_set = await mongo_db.set_user_preferences(str(test_user_id), preferences)
    if not prefs_set:
        logger.error("Failed to set user preferences")
        return False
    logger.info("✅ set_user_preferences successful")
    
    # Get preferences
    retrieved_prefs = await mongo_db.get_user_preferences(str(test_user_id))
    if not retrieved_prefs:
        logger.error("Failed to retrieve user preferences")
        return False
      # Check if all preferences are set correctly
    for key, value in preferences.items():
        if key != "updated_at" and key != "created_at":  # Skip timestamp fields
            if retrieved_prefs.get(key) != value:
                logger.error(f"Preference {key} = {retrieved_prefs.get(key)}, expected {value}")
                return False
    
    logger.info("✅ get_user_preferences successful")
    
    # Step 5: Test conversation history clearing
    logger.info("Testing clear_conversation_history...")
    
    # Clear history (two most recent messages)
    cleared = await mongo_db.clear_conversation_history(conversation_id, 2)
    if not cleared:
        logger.error("Failed to clear conversation history")
        return False
    
    # Check remaining messages
    remaining_messages = await mongo_db.get_conversation_messages(conversation_id)
    if len(remaining_messages) != len(messages) - 2:
        logger.error(f"After clearing, {len(remaining_messages)} messages remain, expected {len(messages) - 2}")
        return False
    
    logger.info(f"✅ clear_conversation_history successful")
    
    # Step 6: Test archiving conversation
    logger.info("Testing archive_conversation...")
    
    archived = await mongo_db.archive_conversation(conversation_id)
    if not archived:
        logger.error("Failed to archive conversation")
        return False
    
    logger.info("✅ archive_conversation successful")
    
    # All tests passed
    logger.info("🎉 All MongoDB integration tests passed!")
    return True

async def main():
    """Main entry point for the MongoDB integration test"""
    try:
        success = await test_mongodb_integration()
        if success:
            print("\n✅ MongoDB integration test successful!")
        else:
            print("\n❌ MongoDB integration test failed!")
    except Exception as e:
        logger.error(f"Error during MongoDB integration test: {e}")
        print("\n❌ MongoDB integration test failed with an exception!")
    finally:
        # Close MongoDB connection
        if hasattr(mongo_db, 'client') and mongo_db.client:
            mongo_db.client.close()

if __name__ == "__main__":
    asyncio.run(main())
