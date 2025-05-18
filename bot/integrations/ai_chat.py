"""
AI Chatbot Integration using OpenRouter API

This module provides integration with OpenRouter's AI models for a Discord chatbot.
It includes features for maintaining conversation context, message clearing, and
channel-specific responses with MongoDB support for persistence.
"""

import os
import aiohttp
import logging
import discord
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bot.utils.config import OPENROUTER_API_KEY, USE_MONGO_FOR_AI

# Import MongoDB utilities if enabled
if USE_MONGO_FOR_AI:
    from bot.utils import mongo_db

# OpenRouter configuration
OPENROUTER_MODEL = "meta-llama/llama-4-maverick:free"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Maximum message history to maintain per channel
MAX_HISTORY_LENGTH = 15
# Maximum retries for API calls
MAX_RETRIES = 3
# Backoff delay for retries (in seconds)
RETRY_DELAY = 2
# Maximum token limit (to prevent context overflow)
MAX_TOKENS = 4000
# Maximum message length for Discord (Discord has a 2000 character limit)
MAX_MESSAGE_LENGTH = 1900

# Store for active AI chat channels (guild_id -> channel_id) - used when MongoDB is disabled
active_channels = {}
# Store for message history (channel_id -> list of messages) - used when MongoDB is disabled
message_history = {}

# Custom exception classes for better error handling
class OpenRouterError(Exception):
    """Base exception class for OpenRouter API errors."""
    pass

class ApiConnectionError(OpenRouterError):
    """Connection errors with the OpenRouter API."""
    pass

class ApiResponseError(OpenRouterError):
    """Error responses from the OpenRouter API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error ({status_code}): {message}")

class ApiRateLimitError(OpenRouterError):
    """Rate limit exceeded errors."""
    pass

class TokenLimitExceededError(OpenRouterError):
    """Token limit exceeded errors."""
    pass

async def set_ai_channel(guild_id: int, channel_id: int, user_id: Optional[int] = None) -> None:
    """
    Set the active AI chat channel for a guild.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID where the AI should respond
        user_id: (Optional) User ID who set the channel
    """
    if USE_MONGO_FOR_AI:
        # Use MongoDB to store the AI channel
        await mongo_db.set_ai_channel(guild_id, channel_id, user_id)
    else:
        # Legacy in-memory storage
        # Remove channel from any other guild (though this shouldn't happen)
        for gid, cid in list(active_channels.items()):
            if cid == channel_id and gid != guild_id:
                del active_channels[gid]
        
        # Set this channel as the active channel for this guild
        active_channels[guild_id] = channel_id
    
    # Initialize or clear message history for this channel
    if USE_MONGO_FOR_AI:
        # In MongoDB, conversation will be created on first message
        pass
    else:
        # Legacy in-memory storage
        message_history[channel_id] = []
    
    logging.info(f"AI chat activated in guild {guild_id}, channel {channel_id}")

def is_ai_channel(guild_id: int, channel_id: int) -> bool:
    """
    Check if the channel is the designated AI chat channel for the guild.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID to check
        
    Returns:
        True if this is the active AI chat channel for this guild
    """
    if USE_MONGO_FOR_AI:
        # Use MongoDB to check
        # Using synchronous check to avoid complications with async in this function
        # This is a bit of a hack, but it works for this simple check
        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(mongo_db.is_ai_channel(guild_id, channel_id))
            return result
        except:
            # Fallback to in-memory if something goes wrong
            return active_channels.get(guild_id) == channel_id
    else:
        return active_channels.get(guild_id) == channel_id

def get_ai_channel(guild_id: int) -> Optional[int]:
    """
    Get the active AI chat channel ID for a guild.
    
    Args:
        guild_id: The Discord guild ID
        
    Returns:
        Channel ID if set, None otherwise
    """
    if USE_MONGO_FOR_AI:
        # Use MongoDB to get the channel
        # Using synchronous check to avoid complications with async in this function
        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(mongo_db.get_ai_channel(guild_id))
            return result
        except:
            # Fallback to in-memory if something goes wrong
            return active_channels.get(guild_id)
    else:
        return active_channels.get(guild_id)

def clear_chat_history(channel_id: int, count: Optional[int] = None) -> bool:
    """
    Clear the message history for a channel.
    
    Args:
        channel_id: The Discord channel ID
        count: Number of most recent messages to clear (None means all)
        
    Returns:
        True if history was cleared, False if channel has no history
    """
    if USE_MONGO_FOR_AI:
        # Using synchronous check to avoid complications with async in this function
        loop = asyncio.get_event_loop()
        try:
            # Get the conversation ID for this channel
            conversation = loop.run_until_complete(mongo_db.ai_conversations.find_one(
                {"channel_id": str(channel_id)},
                sort=[("last_activity", -1)]
            ))
            
            if conversation:
                conversation_id = conversation["_id"]
                # Clear history in MongoDB
                result = loop.run_until_complete(mongo_db.clear_conversation_history(
                    conversation_id, count
                ))
                return result
            else:
                return False
        except Exception as e:
            logging.error(f"Error clearing conversation history from MongoDB: {e}")
            # Fallback to in-memory if MongoDB fails
            pass
    
    # Legacy in-memory clearing
    if channel_id not in message_history:
        return False
    
    if count is None or count >= len(message_history[channel_id]):
        # Clear all history
        message_history[channel_id] = []
    else:
        # Remove only the specified number of most recent messages
        message_history[channel_id] = message_history[channel_id][:-count]
    
    return True

def get_token_estimate(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    This is a simple approximation (about 4 chars per token for English).
    
    Args:
        text: The input text
        
    Returns:
        Estimated token count
    """
    return len(text) // 4 + 1

def truncate_history_if_needed(channel_id: int) -> None:
    """
    Truncate message history if it exceeds token limits.
    
    Args:
        channel_id: The Discord channel ID
    """
    if channel_id not in message_history:
        return
    
    history = message_history[channel_id]
    
    # First check if we exceed the max messages limit
    if len(history) > MAX_HISTORY_LENGTH:
        message_history[channel_id] = history[-MAX_HISTORY_LENGTH:]
        history = message_history[channel_id]
    
    # Then check token count and trim if needed
    total_tokens = sum(get_token_estimate(msg["content"]) for msg in history)
    
    while total_tokens > MAX_TOKENS and len(history) > 1:
        # Remove oldest message
        removed = history.pop(0)
        total_tokens -= get_token_estimate(removed["content"])
        message_history[channel_id] = history

def split_message(message: str) -> List[str]:
    """
    Split a message into chunks that fit within Discord's message length limit.
    
    Args:
        message: The message to split
        
    Returns:
        List of message chunks
    """
    chunks = []
    while message:
        if len(message) <= MAX_MESSAGE_LENGTH:
            chunks.append(message)
            break
        
        # Try to split at a sentence boundary
        split_point = message[:MAX_MESSAGE_LENGTH].rfind('. ') + 1
        if split_point <= 0:  # No suitable sentence break found
            split_point = message[:MAX_MESSAGE_LENGTH].rfind(' ')
        if split_point <= 0:  # No suitable word break found
            split_point = MAX_MESSAGE_LENGTH
        
        chunks.append(message[:split_point])
        message = message[split_point:].lstrip()
    
    return chunks

async def get_ai_response(prompt: str, channel_id: int, system_prompt: str, username: str = None, user_id: str = None, retry_count: int = 0) -> str:
    """
    Get a response from the AI model via OpenRouter.
    
    Args:
        prompt: The user's message
        channel_id: The Discord channel ID
        system_prompt: The system prompt to use for the AI
        username: The username of the message sender (optional)
        user_id: The Discord user ID of the message sender (optional)
        retry_count: Current retry attempt (for internal use)
        
    Returns:
        The AI's response
        
    Raises:
        Various OpenRouterError subclasses for different failure scenarios
    """    
    # Get user preferences if available
    user_preferences = None
    if USE_MONGO_FOR_AI and user_id:
        try:
            user_preferences = await mongo_db.get_user_preferences(user_id)
        except Exception as e:
            logging.error(f"Error retrieving user preferences: {e}")
            # Default preferences will be used
    
    # Customize system prompt based on user preferences
    custom_system_prompt = system_prompt
    if user_preferences:
        # Adjust tone based on preference
        tone_preference = user_preferences.get("tone_preference", "super_casual")
        if tone_preference == "super_casual":
            custom_system_prompt += "\nUse a super casual, friendly tone with emojis and internet slang."
        elif tone_preference == "casual":
            custom_system_prompt += "\nUse a casual, friendly tone."
        elif tone_preference == "neutral":
            custom_system_prompt += "\nUse a neutral, helpful tone."
        elif tone_preference == "formal":
            custom_system_prompt += "\nUse a formal, professional tone."
        
        # Adjust emoji usage
        emoji_level = user_preferences.get("emoji_level", 3)
        if emoji_level == 0:
            custom_system_prompt += "\nDo not use emojis in responses."
        elif emoji_level == 1:
            custom_system_prompt += "\nUse emojis very sparingly (maximum 1-2 per response)."
        elif emoji_level == 2:
            custom_system_prompt += "\nUse a moderate number of emojis (3-5 per response)."
        elif emoji_level == 3:
            custom_system_prompt += "\nUse plenty of emojis throughout your responses."
        
        # Adjust username mention preference
        mention_name = user_preferences.get("mention_name", True)
        if not mention_name:
            custom_system_prompt += "\nDo not address the user by name at the start of responses."
    
    # Prepare chat history for context
    messages = []
    
    # Start with system prompt
    messages.append({"role": "system", "content": custom_system_prompt})
    
    if USE_MONGO_FOR_AI:
        # For DM channels, we add a prefix
        is_dm = not str(channel_id).isdigit() and str(channel_id).startswith("dm_")
        
        # Get or create conversation
        try:
            conversation_id = await mongo_db.get_or_create_conversation(
                str(channel_id),
                None if is_dm else str(channel_id).split('_')[0] if '_' in str(channel_id) else None,
                user_id,
                is_dm
            )
            
            if conversation_id:
                # Get message history from MongoDB
                history_messages = await mongo_db.get_conversation_messages(conversation_id, MAX_HISTORY_LENGTH)
                
                # Format messages for the OpenRouter API
                for msg in history_messages:
                    content = msg["content"]
                    if msg.get("username") and msg["role"] == "user":
                        content = f"[{msg['username']}]: {content}"
                        
                        # Add hint for multi-user conversations
                        if user_id and msg.get("user_id") and str(msg["user_id"]) != str(user_id):
                            content = f"{content} [Different user from the current conversation]"
                    
                    messages.append({"role": msg["role"], "content": content})
        except Exception as e:
            logging.error(f"Error retrieving message history from MongoDB: {e}")
            # Continue with just the current message
            pass
    else:
        # Use in-memory message history
        if channel_id in message_history:
            for msg in message_history[channel_id]:
                content = msg["content"]
                # If the message includes username info, format it appropriately
                if msg.get("username") and msg["role"] == "user":
                    content = f"[{msg['username']}]: {content}"
                    
                    # If this is not from the current user, add a hint to help the AI track multiple conversations
                    if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                        content = f"{content} [Different user from the current conversation]"
                messages.append({"role": msg["role"], "content": content})
    
    # Add the current prompt with username if available
    user_content = prompt
    if username:
        user_content = f"[{username}]: {prompt}"
    messages.append({"role": "user", "content": user_content})
    
    # Make the API request
    ai_response = await _make_openrouter_request(messages, retry_count)
    
    # Store messages in history
    if USE_MONGO_FOR_AI:
        try:
            if conversation_id:
                # Add user message
                await mongo_db.add_message(
                    conversation_id,
                    "user",
                    prompt,
                    user_id,
                    username
                )
                
                # Add AI response
                await mongo_db.add_message(
                    conversation_id,
                    "assistant",
                    ai_response
                )
        except Exception as e:
            logging.error(f"Error storing messages in MongoDB: {e}")
            # Fallback to in-memory
            if channel_id not in message_history:
                message_history[channel_id] = []
            
            # Add user message
            user_message = {"role": "user", "content": prompt}
            if username:
                user_message["username"] = username
            if user_id:
                user_message["user_id"] = user_id
            message_history[channel_id].append(user_message)
            
            # Add AI response
            message_history[channel_id].append({"role": "assistant", "content": ai_response})
            truncate_history_if_needed(channel_id)
    else:
        # Legacy in-memory storage
        # Initialize channel history if it doesn't exist
        if channel_id not in message_history:
            message_history[channel_id] = []
        
        # Add user message
        user_message = {"role": "user", "content": prompt}
        if username:
            user_message["username"] = username
        if user_id:
            user_message["user_id"] = user_id
        message_history[channel_id].append(user_message)
        
        # Add AI response
        message_history[channel_id].append({"role": "assistant", "content": ai_response})
        
        # Ensure we don't exceed token limits
        truncate_history_if_needed(channel_id)
    
    return ai_response

async def _make_openrouter_request(messages: List[Dict[str, str]], retry_count: int = 0) -> str:
    """
    Make a request to the OpenRouter API.
    
    Args:
        messages: List of message objects for the API
        retry_count: Current retry attempt
        
    Returns:
        The AI's response text
        
    Raises:
        Various OpenRouterError subclasses for different failure scenarios
    """
    # Prepare the request payload
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 1024  # Limit the response length
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://discord-reddit-meme-bot.example.com"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_API_URL, 
                headers=headers, 
                json=payload,
                timeout=30  # 30 second timeout
            ) as response:
                response_text = await response.text()
                
                # Handle various error cases
                if response.status == 429:
                    # Rate limit error
                    raise ApiRateLimitError("Rate limit exceeded. Please try again later.")
                
                elif response.status == 400:
                    # Check if it's a token limit error
                    try:
                        error_data = json.loads(response_text)
                        if "token limit" in error_data.get("error", {}).get("message", "").lower():
                            raise TokenLimitExceededError("Token limit exceeded. Try clearing some message history.")
                    except (json.JSONDecodeError, KeyError):
                        pass
                    
                    # Generic 400 error
                    raise ApiResponseError(response.status, f"Bad request: {response_text}")
                
                elif response.status != 200:
                    raise ApiResponseError(response.status, response_text)
                
                # Parse the response
                try:
                    data = json.loads(response_text)
                    return data["choices"][0]["message"]["content"]
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    raise ApiResponseError(response.status, f"Failed to parse API response: {str(e)}")
    
    except aiohttp.ClientError as e:
        # Network-related errors
        if retry_count < MAX_RETRIES:
            # Exponential backoff
            await asyncio.sleep(RETRY_DELAY * (2 ** retry_count))
            return await _make_openrouter_request(messages, retry_count + 1)
        else:
            raise ApiConnectionError(f"Failed to connect to OpenRouter API after {MAX_RETRIES} attempts: {str(e)}")
    
    except (ApiRateLimitError, TokenLimitExceededError):
        # Pass through these specific exceptions
        raise
    
    except Exception as e:
        # Any other unexpected errors
        logging.error(f"Unexpected error in AI API request: {str(e)}")
        raise OpenRouterError(f"An unexpected error occurred: {str(e)}")

def format_error_message(error: Exception) -> str:
    """
    Format an error message for user display based on exception type.
    
    Args:
        error: The exception that occurred
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, ApiRateLimitError):
        return "⚠️ **Rate Limit Exceeded**\nThe AI service is currently busy. Please try again in a few minutes."
    
    elif isinstance(error, TokenLimitExceededError):
        return "⚠️ **Context Limit Exceeded**\nOur conversation has gotten too long. Try using `/clear_chat` to reset it."
    
    elif isinstance(error, ApiConnectionError):
        return "❌ **Connection Error**\nFailed to connect to the AI service. Please check your internet connection and try again."
    
    elif isinstance(error, ApiResponseError):
        if error.status_code == 401 or error.status_code == 403:
            return "❌ **Authentication Error**\nThe bot's AI service authentication failed. Please notify the bot owner."
        else:
            return f"❌ **API Error**\nThe AI service returned an error (HTTP {error.status_code}). Please try again later."
    
    else:
        return "❌ **Unexpected Error**\nSomething went wrong with the AI chatbot. Please try again or contact the bot owner if the issue persists."

# Helper function to create embeds for AI responses
def create_ai_response_embed(response: str, username: str) -> discord.Embed:
    """
    Create an embed for the AI response.
    
    Args:
        response: The AI's response text
        username: The username who triggered the response
        
    Returns:
        Formatted Discord embed
    """
    # Format the response to make sure it starts with addressing the user if it doesn't already
    if not any(marker in response[:30].lower() for marker in [username.lower(), "hey", "yo", "hi ", "hello", "sup"]):
        response = f"@{username} {response}"
    
    embed = discord.Embed(
        description=response,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.set_author(name="Nite 🌙")
    embed.set_footer(text=f"Chatting with {username} • Using Llama 4 Maverick")
    return embed

async def set_user_preference(user_id: str, preference_key: str, preference_value: Any) -> bool:
    """
    Set a preference for a user's AI chat experience.
    
    Args:
        user_id: The user's Discord ID
        preference_key: The preference to set (e.g., 'tone_preference', 'emoji_level')
        preference_value: The value to set for the preference
        
    Returns:
        True if set successfully, False otherwise
    """
    if not USE_MONGO_FOR_AI:
        logging.warning("User preferences require MongoDB. Enable USE_MONGO_FOR_AI in config.")
        return False
    
    try:
        # Get current preferences
        current_preferences = await mongo_db.get_user_preferences(user_id)
        
        # Update the specific preference
        current_preferences[preference_key] = preference_value
        
        # Save the updated preferences
        return await mongo_db.set_user_preferences(user_id, current_preferences)
    except Exception as e:
        logging.error(f"Error setting user preference: {e}")
        return False
        
async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get a user's AI chat preferences.
    
    Args:
        user_id: The user's Discord ID
        
    Returns:
        Dictionary of preferences or default preferences if not set
    """
    if not USE_MONGO_FOR_AI:
        logging.warning("User preferences require MongoDB. Enable USE_MONGO_FOR_AI in config.")
        return mongo_db.get_default_preferences()
    
    try:
        return await mongo_db.get_user_preferences(user_id)
    except Exception as e:
        logging.error(f"Error getting user preferences: {e}")
        return mongo_db.get_default_preferences()
