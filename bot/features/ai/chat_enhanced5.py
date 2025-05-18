"""
AI Chatbot Integration using OpenRouter API - Enhanced Version 5

This module provides integration with OpenRouter's AI models for a Discord chatbot.
It includes features for maintaining conversation context, message clearing, and
channel-specific responses with MongoDB support for persistence.

Enhanced with:
- Thread creation and management
- Markdown formatting
- Long response handling
- Table formatting
- Natural language command recognition
- Multimodal content support (text + images)
"""

import aiohttp
import logging
import discord
import asyncio
import re
import io
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from bot.core.config import OPENROUTER_API_KEY, USE_MONGO_FOR_AI

# Import MongoDB utilities if enabled
if USE_MONGO_FOR_AI:
    from bot.utils import mongo_db

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-4-maverick"
MAX_HISTORY_TOKENS = 4000  # Approximate token limit for history
MAX_MESSAGE_LENGTH = 2000  # Discord's message length limit
MAX_LONG_MESSAGE = 4000    # Threshold for very long messages

# In-memory storage for chat channels and message history
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

def format_markdown(text: str) -> str:
    """
    Ensure proper markdown formatting in the response.

    Args:
        text: The text to format

    Returns:
        Properly formatted markdown text
    """
    # Fix code blocks that don't have language specification
    text = re.sub(r'```(?!\w+\n)', '```text\n', text)

    # Ensure code blocks are properly closed
    open_blocks = text.count('```')
    if open_blocks % 2 != 0:
        text += '\n```'

    return text

def handle_long_response(response: str, filename_prefix: str = "response") -> Tuple[List[str], Optional[discord.File]]:
    """
    Handle long responses by either splitting them into multiple messages or creating a file attachment.

    Args:
        response: The AI's response text
        filename_prefix: Prefix for the filename if a file is created

    Returns:
        Tuple of (message_parts, file_attachment)
    """
    # For very long responses, create a text file
    if len(response) > MAX_LONG_MESSAGE:
        # Extract a summary from the beginning of the response
        summary_match = re.search(r'^.*?(?:\.|$)', response.strip())
        summary = summary_match.group(0) if summary_match else "Here's a detailed response"

        # Create a text file with the full response
        file_content = response.encode('utf-8')
        file = discord.File(
            io.BytesIO(file_content),
            filename=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        # Return the summary and the file
        return [f"{summary}... (see attached file for complete response)"], file

    # For normal responses, just return them as is
    return [response], None

async def _make_openrouter_request(messages: List[Dict[str, Any]], retry_count: int = 0) -> str:
    """
    Make a request to the OpenRouter API, supporting multimodal content (text and images).

    Args:
        messages: List of message objects for the API, which may include multimodal content
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

async def get_ai_response(
    prompt: str,
    channel_id: int,
    system_prompt: str,
    username: str = None,
    user_id: str = None,
    image_urls: List[str] = None,
    retry_count: int = 0
) -> Union[str, Tuple[List[str], Optional[discord.File]]]:
    """
    Get a response from the AI model via OpenRouter, supporting both text and image inputs.
    Enhanced with markdown formatting, thread creation, and long response handling.

    Args:
        prompt: The user's message
        channel_id: The Discord channel ID
        system_prompt: The system prompt to use for the AI
        username: The username of the message sender (optional)
        user_id: The Discord user ID of the message sender (optional)
        image_urls: List of image URLs to process (optional)
        retry_count: Current retry attempt (for internal use)

    Returns:
        Either a string response or a tuple of (message_parts, file_attachment)
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
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        except Exception as e:
            logging.error(f"Error retrieving MongoDB message history: {e}")
            # Fall back to in-memory history
            if channel_id in message_history:
                for msg in message_history[channel_id]:
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    else:
        # Legacy in-memory storage
        if channel_id in message_history:
            for msg in message_history[channel_id]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Add the current prompt with username if available
    user_content = prompt
    if username:
        user_content = f"{username}, {prompt}"

    # Track if this message has an image
    has_image = image_urls and len(image_urls) > 0

    # Handle image URLs if provided
    if has_image:
        # Create a multimodal message with text and images
        content_parts = []

        # Add text content if it exists
        if user_content:
            content_parts.append({
                "type": "text",
                "text": user_content
            })

        # Add image URLs
        for image_url in image_urls:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })

        # Add the multimodal message
        messages.append({
            "role": "user",
            "content": content_parts
        })
    else:
        # Text-only message
        messages.append({"role": "user", "content": user_content})

    # Make the API request
    ai_response = await _make_openrouter_request(messages, retry_count)

    # Format the response with proper markdown
    ai_response = format_markdown(ai_response)

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
                    username,
                    has_image
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
            user_message = {
                "role": "user",
                "content": prompt,
                "had_image": has_image
            }
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
        user_message = {
            "role": "user",
            "content": prompt,
            "had_image": has_image
        }
        if username:
            user_message["username"] = username
        if user_id:
            user_message["user_id"] = user_id
        message_history[channel_id].append(user_message)

        # Add AI response
        message_history[channel_id].append({"role": "assistant", "content": ai_response})

        # Ensure we don't exceed token limits
        truncate_history_if_needed(channel_id)

    # Handle long responses
    if len(ai_response) > MAX_MESSAGE_LENGTH:
        return handle_long_response(ai_response, f"response_{username or 'ai'}")

    # For thread creation, we'll return just the response text
    # The thread creation will be handled in the calling function
    return ai_response



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
