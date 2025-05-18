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
from bot.core.config import OPENROUTER_API_KEY, USE_MONGO_FOR_AI

# Import MongoDB utilities if enabled
if USE_MONGO_FOR_AI:
    from bot.utils import mongo_db

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-4-maverick"
MAX_HISTORY_TOKENS = 4000  # Approximate token limit for history

# In-memory storage for chat channels and message history
ai_channels = {}  # guild_id -> channel_id
message_history = {}  # channel_id -> [messages]

# Custom exceptions
class OpenRouterError(Exception):
    """Base exception for OpenRouter API errors"""
    pass

class OpenRouterAPIKeyError(OpenRouterError):
    """Exception for API key issues"""
    pass

class OpenRouterRateLimitError(OpenRouterError):
    """Exception for rate limit issues"""
    pass

class OpenRouterServerError(OpenRouterError):
    """Exception for server-side errors"""
    pass

# Channel management functions
def set_ai_channel(guild_id: int, channel_id: int) -> Tuple[bool, Optional[int]]:
    """
    Set a channel as the AI chat channel for a guild.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID
        
    Returns:
        Tuple of (success, previous_channel_id)
    """
    previous = ai_channels.get(guild_id)
    ai_channels[guild_id] = channel_id
    
    # Store in MongoDB if enabled
    if USE_MONGO_FOR_AI:
        try:
            asyncio.create_task(mongo_db.set_ai_channel(guild_id, channel_id))
        except Exception as e:
            logging.error(f"Error storing AI channel in MongoDB: {e}")
    
    return True, previous

def is_ai_channel(guild_id: int, channel_id: int) -> bool:
    """
    Check if a channel is the designated AI chat channel for a guild.
    
    Args:
        guild_id: The Discord guild ID
        channel_id: The Discord channel ID
        
    Returns:
        True if this is the AI chat channel, False otherwise
    """
    return ai_channels.get(guild_id) == channel_id

def get_ai_channel(guild_id: int) -> Optional[int]:
    """
    Get the AI chat channel ID for a guild.
    
    Args:
        guild_id: The Discord guild ID
        
    Returns:
        The channel ID or None if not set
    """
    return ai_channels.get(guild_id)

# Message history management
def clear_chat_history(channel_id: int, count: Optional[int] = None) -> bool:
    """
    Clear chat history for a channel.
    
    Args:
        channel_id: The Discord channel ID
        count: Optional number of recent messages to clear
        
    Returns:
        True if history was cleared, False if no history existed
    """
    if USE_MONGO_FOR_AI:
        try:
            # This is async but we're calling from a sync context
            # Create a task to handle it
            asyncio.create_task(mongo_db.clear_conversation(channel_id, count))
            return True
        except Exception as e:
            logging.error(f"Error clearing MongoDB chat history: {e}")
            # Fall back to in-memory if MongoDB fails
    
    # In-memory fallback
    if channel_id not in message_history:
        return False
        
    if count is None:
        # Clear all history
        message_history[channel_id] = []
    else:
        # Clear only the specified number of messages
        # We need to keep system messages and remove user/assistant messages
        history = message_history[channel_id]
        system_messages = [msg for msg in history if msg["role"] == "system"]
        other_messages = [msg for msg in history if msg["role"] != "system"]
        
        # Keep all system messages and remove 'count' user/assistant messages
        if len(other_messages) <= count:
            # If we have fewer messages than count, just keep system messages
            message_history[channel_id] = system_messages
        else:
            # Keep system messages and older user/assistant messages
            message_history[channel_id] = system_messages + other_messages[:-count]
    
    return True

def truncate_history_if_needed(channel_id: int):
    """
    Ensure the message history doesn't exceed token limits.
    
    Args:
        channel_id: The Discord channel ID
    """
    if channel_id not in message_history:
        return
        
    history = message_history[channel_id]
    
    # Simple heuristic: assume average of 5 tokens per word
    total_tokens = sum(len(msg.get("content", "").split()) * 5 for msg in history)
    
    # If we're over the limit, remove oldest messages (except system messages)
    while total_tokens > MAX_HISTORY_TOKENS and len(history) > 1:
        # Find the first non-system message
        for i, msg in enumerate(history):
            if msg["role"] != "system":
                # Remove this message
                removed = history.pop(i)
                # Update token count
                removed_tokens = len(removed.get("content", "").split()) * 5
                total_tokens -= removed_tokens
                break

# Message formatting helpers
def split_message(message: str, max_length: int = 2000) -> List[str]:
    """
    Split a message into chunks that fit within Discord's message length limit.
    
    Args:
        message: The message to split
        max_length: Maximum length of each chunk
        
    Returns:
        List of message chunks
    """
    if len(message) <= max_length:
        return [message]
        
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = message.split("\n\n")
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, start a new chunk
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
                
            # If the paragraph itself is too long, split it further
            if len(paragraph) > max_length:
                # Split by sentences
                sentences = paragraph.replace(". ", ".\n").split("\n")
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                            
                        # If the sentence is still too long, split by words
                        if len(sentence) > max_length:
                            words = sentence.split(" ")
                            for word in words:
                                if len(current_chunk) + len(word) + 1 > max_length:
                                    chunks.append(current_chunk)
                                    current_chunk = word + " "
                                else:
                                    current_chunk += word + " "
                        else:
                            current_chunk = sentence + " "
                    else:
                        current_chunk += sentence + " "
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def format_error_message(error: Exception) -> str:
    """
    Format an error message for display to users.
    
    Args:
        error: The exception that occurred
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, OpenRouterAPIKeyError):
        return "⚠️ API key error. Please check your OpenRouter API key configuration."
    elif isinstance(error, OpenRouterRateLimitError):
        return "⚠️ Rate limit exceeded. Please try again in a few minutes."
    elif isinstance(error, OpenRouterServerError):
        return "⚠️ OpenRouter server error. Please try again later."
    elif isinstance(error, OpenRouterError):
        return f"⚠️ OpenRouter API error: {str(error)}"
    else:
        return f"⚠️ An error occurred: {str(error)}"

def create_ai_response_embed(content: str, username: Optional[str] = None) -> discord.Embed:
    """
    Create a Discord embed for an AI response.
    
    Args:
        content: The AI response content
        username: Optional username to mention
        
    Returns:
        Discord embed
    """
    embed = discord.Embed(
        description=content,
        color=discord.Color.blue()
    )
    
    if username:
        embed.set_author(name=f"Response to {username}")
    else:
        embed.set_author(name="AI Assistant")
        
    embed.set_footer(text="Powered by Llama 4 Maverick")
    
    return embed

# Main AI interaction function
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
    """
    # Prepare messages for the API
    messages = []
    
    # Add system prompt
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history
    conversation_id = None
    if USE_MONGO_FOR_AI:
        try:
            # Get conversation ID for this channel
            conversation_id = await mongo_db.get_conversation_id(channel_id)
            
            # If no conversation exists, create one
            if not conversation_id:
                conversation_id = await mongo_db.create_conversation(channel_id)
                
            # Get message history
            history = await mongo_db.get_messages(conversation_id, limit=20)
            
            # Add messages to the context
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # If this is not from the current user, add a hint to help the AI track multiple conversations
                if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                    content = f"{content} [Different user from the current conversation]"
                messages.append({"role": role, "content": content})
        except Exception as e:
            logging.error(f"Error retrieving MongoDB message history: {e}")
            # Fall back to in-memory history
            if channel_id in message_history:
                for msg in message_history[channel_id]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    # If this is not from the current user, add a hint to help the AI track multiple conversations
                    if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                        content = f"{content} [Different user from the current conversation]"
                    messages.append({"role": msg["role"], "content": content})
    else:
        # Legacy in-memory storage
        if channel_id in message_history:
            for msg in message_history[channel_id]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # If this is not from the current user, add a hint to help the AI track multiple conversations
                if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                    content = f"{content} [Different user from the current conversation]"
                messages.append({"role": role, "content": content})
    
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
            async with session.post(OPENROUTER_API_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    # Successful response
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status == 401:
                    # Authentication error
                    raise OpenRouterAPIKeyError("Invalid API key")
                elif response.status == 429:
                    # Rate limit error
                    if retry_count < 2:
                        # Wait and retry
                        await asyncio.sleep(2 ** retry_count)
                        return await _make_openrouter_request(messages, retry_count + 1)
                    else:
                        raise OpenRouterRateLimitError("Rate limit exceeded")
                elif response.status >= 500:
                    # Server error
                    if retry_count < 2:
                        # Wait and retry
                        await asyncio.sleep(2 ** retry_count)
                        return await _make_openrouter_request(messages, retry_count + 1)
                    else:
                        raise OpenRouterServerError(f"Server error: {response.status}")
                else:
                    # Other error
                    error_text = await response.text()
                    raise OpenRouterError(f"API error: {response.status} - {error_text}")
    except aiohttp.ClientError as e:
        # Network error
        if retry_count < 2:
            # Wait and retry
            await asyncio.sleep(2 ** retry_count)
            return await _make_openrouter_request(messages, retry_count + 1)
        else:
            raise OpenRouterError(f"Network error: {str(e)}")

# User preferences
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
