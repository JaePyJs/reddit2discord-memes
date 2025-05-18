"""
AI Chatbot Integration using OpenRouter API

This module provides integration with OpenRouter's AI models for a Discord chatbot.
It includes features for maintaining conversation context, message clearing, and
channel-specific responses with MongoDB support for persistence.

Enhanced with:
- Thread creation and management
- Markdown formatting
- Long response handling
- Table formatting
- Natural language command recognition
"""

import aiohttp
import logging
import discord
import asyncio
import re
import io
import random
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
THREAD_COMMAND_PATTERN = re.compile(r'(?:^|\s)!(?:thread|createthread)(?:\s|$)', re.IGNORECASE)
DELETE_COMMAND_PATTERN = re.compile(r'(?:delete|remove)\s+(?:the\s+)?(?:last\s+)?(\d+)(?:\s+messages?)?', re.IGNORECASE)

# In-memory storage for chat channels and message history
ai_channels = {}  # guild_id -> channel_id
message_history = {}  # channel_id -> [messages]
active_threads = {}  # thread_id -> parent_channel_id

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

def register_thread(thread_id: int, parent_channel_id: int) -> None:
    """
    Register a thread as being associated with an AI chat channel.

    Args:
        thread_id: The Discord thread ID
        parent_channel_id: The parent channel ID
    """
    active_threads[thread_id] = parent_channel_id

def is_ai_thread(thread_id: int) -> bool:
    """
    Check if a thread is associated with an AI chat channel.

    Args:
        thread_id: The Discord thread ID

    Returns:
        True if this is an AI thread, False otherwise
    """
    return thread_id in active_threads

def get_thread_parent(thread_id: int) -> Optional[int]:
    """
    Get the parent channel ID for an AI thread.

    Args:
        thread_id: The Discord thread ID

    Returns:
        The parent channel ID or None if not found
    """
    return active_threads.get(thread_id)

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
def split_message(message: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Split a message into chunks that fit within Discord's message length limit.
    Improved to split at logical break points like paragraphs and sections.

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

    # Check if the message contains code blocks
    code_blocks = re.findall(r'```[\s\S]*?```', message)
    if code_blocks:
        # Split by code blocks first
        parts = re.split(r'(```[\s\S]*?```)', message)
        for part in parts:
            # If this is a code block
            if part.startswith('```') and part.endswith('```'):
                # If adding this code block would exceed the limit, start a new chunk
                if len(current_chunk) + len(part) > max_length:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""

                    # If the code block itself is too long, split it
                    if len(part) > max_length:
                        # Extract language if specified
                        match = re.match(r'```(\w*)\n', part)
                        language = match.group(1) if match else ""

                        # Remove the opening and closing ticks
                        code_content = part[3 + len(language):].strip()
                        if code_content.endswith('```'):
                            code_content = code_content[:-3].strip()

                        # Split the code content
                        code_lines = code_content.split('\n')
                        code_chunk = f"```{language}\n"

                        for line in code_lines:
                            if len(code_chunk) + len(line) + 1 > max_length - 4:  # -4 for the closing ```
                                chunks.append(code_chunk + "\n```")
                                code_chunk = f"```{language}\n{line}"
                            else:
                                code_chunk += line + "\n"

                        if code_chunk != f"```{language}\n":
                            chunks.append(code_chunk + "```")
                    else:
                        chunks.append(part)
                else:
                    current_chunk += part
            else:
                # Regular text - split by paragraphs
                paragraphs = part.split("\n\n")
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
    else:
        # No code blocks - split by paragraphs
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

    # For moderately long responses, split them into multiple messages
    elif len(response) > MAX_MESSAGE_LENGTH:
        return split_message(response), None

    # For normal responses, just return them as is
    else:
        return [response], None

def format_markdown(text: str, message: Optional[discord.Message] = None) -> str:
    """
    Ensure proper markdown formatting in the response.

    Args:
        text: The text to format
        message: Optional Discord message for context (used for user mentions)

    Returns:
        Properly formatted markdown text
    """
    # Fix code blocks that don't have language specification
    text = re.sub(r'```(?!\w+\n)', '```text\n', text)

    # Ensure code blocks are properly closed
    open_blocks = text.count('```')
    if open_blocks % 2 != 0:
        text += '\n```'

    # Convert @username mentions to proper Discord mentions if message is provided
    if message and message.guild:
        # Find all potential mentions in the format @username
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text)

        for username in mentions:
            # Try to find the member in the guild
            member = discord.utils.find(
                lambda m: m.display_name.lower() == username.lower() or
                          m.name.lower() == username.lower(),
                message.guild.members
            )

            if member:
                # Replace @username with proper Discord mention without a comma
                text = re.sub(
                    f'@{username}\\b',
                    f'<@{member.id}>',
                    text
                )

        # Also check for direct username mentions without @ symbol
        # This helps with the common case where the AI just uses the username without @
        if message.author:
            # Try to replace the message author's name with a mention
            author_name = message.author.display_name
            # Use word boundary to avoid partial matches
            text = re.sub(
                f'\\b{re.escape(author_name)}\\b(?!,)',  # Match name not followed by comma
                f'<@{message.author.id}>',
                text
            )

    # Remove table formatting attempts - tables don't render well in Discord
    lines = text.split('\n')
    filtered_lines = []
    in_table = False
    table_content = []

    for i, line in enumerate(lines):
        # Detect table header or separator row
        if '|' in line and (i > 0 and '|' in lines[i-1]):
            # Check if this is a separator row (---|---|---)
            if re.match(r'\|[\s-]*\|', line):
                in_table = True
                table_content.append(lines[i-1])  # Add the header row
                continue

        # If we're in a table and this line has pipes
        if in_table and '|' in line:
            table_content.append(line)
            continue

        # If we were in a table but this line doesn't have pipes
        if in_table and (not line.strip() or '|' not in line):
            in_table = False
            # Convert table to plain text
            if table_content:
                filtered_lines.append("**Note:** Table converted to plain text:")
                for table_line in table_content:
                    # Clean up the table row and add as plain text
                    cleaned = table_line.replace('|', ' | ').strip()
                    if cleaned.startswith('|'):
                        cleaned = cleaned[1:]
                    if cleaned.endswith('|'):
                        cleaned = cleaned[:-1]
                    filtered_lines.append(cleaned.strip())
                filtered_lines.append("")  # Add a blank line after the table
                table_content = []

        # Regular non-table line
        if not in_table:
            filtered_lines.append(line)

    # Handle case where table is at the end of the text
    if in_table and table_content:
        filtered_lines.append("**Note:** Table converted to plain text:")
        for table_line in table_content:
            # Clean up the table row and add as plain text
            cleaned = table_line.replace('|', ' | ').strip()
            if cleaned.startswith('|'):
                cleaned = cleaned[1:]
            if cleaned.endswith('|'):
                cleaned = cleaned[:-1]
            filtered_lines.append(cleaned.strip())

    return '\n'.join(filtered_lines)

def create_table_markdown(headers: List[str], rows: List[List[str]]) -> str:
    """
    Create a plain text representation of tabular data since Discord doesn't render markdown tables well.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell values

    Returns:
        Plain text representation of the data
    """
    if not headers or not rows:
        return ""

    result = "**Table Data:**\n\n"

    # Add headers
    result += " | ".join(headers) + "\n"
    result += "-" * 40 + "\n"  # Separator line

    # Add rows
    for row in rows:
        # Ensure row has the same number of columns as headers
        while len(row) < len(headers):
            row.append("")
        result += " | ".join(row) + "\n"

    return result

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

async def create_thread_for_topic(message: discord.Message, topic: str) -> Optional[discord.Thread]:
    """
    Create a new thread for a specific topic.

    Args:
        message: The Discord message to create a thread from
        topic: The topic/name for the thread

    Returns:
        The created thread or None if creation failed
    """
    try:
        # Create a thread with the given topic as the name
        thread = await message.create_thread(
            name=topic[:100],  # Discord has a 100 character limit for thread names
            auto_archive_duration=1440  # Archive after 24 hours of inactivity
        )

        # Register the thread as an AI thread
        if message.channel.id:
            register_thread(thread.id, message.channel.id)

        return thread
    except Exception as e:
        logging.error(f"Error creating thread: {e}")
        return None

def should_create_thread(prompt: str) -> bool:
    """
    Determine if a thread should be created based on the user's message.

    Args:
        prompt: The user's message

    Returns:
        True if a thread should be created, False otherwise
    """
    # Check for explicit thread command
    if THREAD_COMMAND_PATTERN.search(prompt):
        return True

    # Check for complex questions that might benefit from a thread
    complex_indicators = [
        r'\?.*\?',  # Multiple questions
        r'how (can|do|would|could|should) I',  # How-to questions
        r'explain .{10,}',  # Explanation requests
        r'what (is|are) the (steps|ways|methods)',  # Process questions
        r'compare .{5,} (to|and|with) .{5,}',  # Comparison requests
        r'difference between .{5,} and .{5,}',  # Difference questions
    ]

    for pattern in complex_indicators:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True

    # Check message length - longer messages might indicate complex topics
    if len(prompt.split()) > 30:
        return True

    return False

def extract_thread_topic(prompt: str) -> str:
    """
    Extract a suitable topic name for a thread from the user's message.

    Args:
        prompt: The user's message

    Returns:
        A suitable topic name
    """
    # Remove the thread command if present
    cleaned_prompt = THREAD_COMMAND_PATTERN.sub('', prompt).strip()

    # Try to extract a question
    question_match = re.search(r'([^.!?]+\?)', cleaned_prompt)
    if question_match:
        return question_match.group(1).strip()

    # Try to extract the first sentence
    sentence_match = re.search(r'^([^.!?]+[.!?])', cleaned_prompt)
    if sentence_match:
        return sentence_match.group(1).strip()

    # If all else fails, use the first 50 characters
    return cleaned_prompt[:50].strip() + "..."

async def process_natural_language_command(message: discord.Message, prompt: str) -> Tuple[bool, Optional[str]]:
    """
    Process natural language commands embedded in the user's message.

    Args:
        message: The Discord message containing the command
        prompt: The user's message text

    Returns:
        Tuple of (command_processed, response_message)
    """
    # Check for message deletion command
    delete_match = DELETE_COMMAND_PATTERN.search(prompt)
    if delete_match:
        # Ignore deletion commands from users without permissions
        if not message.author.guild_permissions.manage_messages:
            return False, None  # Don't process as a command, let the AI respond normally

        try:
            # Get the number of messages to delete
            count = int(delete_match.group(1))
            if count < 1 or count > 100:
                return True, "I can only delete between 1 and 100 messages at a time."

            # Delete the messages without confirmation for now
            # This is a simpler approach that avoids the wait_for complexity
            deleted = await message.channel.purge(limit=count + 1)  # +1 to include the command message
            return True, f"Deleted {len(deleted) - 1} messages."
        except Exception as e:
            logging.error(f"Error deleting messages: {e}")
            return True, f"Error deleting messages: {str(e)}"

    # Check for thread creation command
    if "create a thread" in prompt.lower() or "start a thread" in prompt.lower():
        # Extract the topic
        topic_match = re.search(r'(about|on|for) ["\']?([^"\']+)["\']?', prompt)
        topic = topic_match.group(2) if topic_match else extract_thread_topic(prompt)

        # Create the thread
        thread = await create_thread_for_topic(message, topic)
        if thread:
            return True, f"Created a new thread: {thread.mention}"
        else:
            return True, "I couldn't create a thread. Please try again."

    # No command found
    return False, None

# Main AI interaction function
async def get_ai_response(
    prompt: str,
    channel_id: int,
    system_prompt: str,
    username: str = None,
    user_id: str = None,
    image_urls: List[str] = None,
    original_message: discord.Message = None,
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
        original_message: The original Discord message object for reply functionality (optional)
        retry_count: Current retry attempt (for internal use)

    Returns:
        Either a string response or a tuple of (message_parts, file_attachment)
    """
    # Check if this is a natural language command
    if original_message:
        command_processed, command_response = await process_natural_language_command(original_message, prompt)
        if command_processed:
            return command_response

    # Check if we should create a thread for this message (handled in the calling function)
    if original_message and should_create_thread(prompt):
        # Thread creation will be handled by the calling function
        # Just log that we detected a thread-worthy message
        logging.debug(f"Thread-worthy message detected: {extract_thread_topic(prompt)}")

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

                # If this is from a different user, add their username to help the AI track multiple conversations
                if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                    if msg.get("username"):
                        content = f"{msg.get('username')} {content}"
                    else:
                        content = f"Different user {content}"
                elif role == "user" and msg.get("username"):
                    # Also add username for the current user's past messages for consistency
                    content = f"{msg.get('username')} {content}"

                # Check if this message had an image
                if msg.get("had_image", False):
                    content = f"{content} [Shared an image]"

                messages.append({"role": role, "content": content})
        except Exception as e:
            logging.error(f"Error retrieving MongoDB message history: {e}")
            # Fall back to in-memory history
            if channel_id in message_history:
                for msg in message_history[channel_id]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")

                    # If this is from a different user, add their username to help the AI track multiple conversations
                    if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                        if msg.get("username"):
                            content = f"{msg.get('username')} {content}"
                        else:
                            content = f"Different user {content}"
                    elif role == "user" and msg.get("username"):
                        # Also add username for the current user's past messages for consistency
                        content = f"{msg.get('username')} {content}"

                    # Check if this message had an image
                    if msg.get("had_image", False):
                        content = f"{content} [Shared an image]"

                    messages.append({"role": role, "content": content})
    else:
        # Legacy in-memory storage
        if channel_id in message_history:
            for msg in message_history[channel_id]:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                # If this is from a different user, add their username to help the AI track multiple conversations
                if user_id and msg.get("user_id") and msg.get("user_id") != user_id:
                    if msg.get("username"):
                        content = f"{msg.get('username')} {content}"
                    else:
                        content = f"Different user {content}"
                elif role == "user" and msg.get("username"):
                    # Also add username for the current user's past messages for consistency
                    content = f"{msg.get('username')} {content}"

                # Check if this message had an image
                if msg.get("had_image", False):
                    content = f"{content} [Shared an image]"

                messages.append({"role": role, "content": content})


    # Add the current prompt with username if available
    user_content = prompt
    if username:
        user_content = f"{username} {prompt}"

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

    # Format the response with proper markdown and handle user mentions
    ai_response = format_markdown(ai_response, original_message)

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

                # Optimize storage periodically (every 10 messages)
                # This helps keep the database efficient
                if random.random() < 0.1:  # 10% chance to optimize on each message
                    asyncio.create_task(mongo_db.optimize_conversation_storage(channel_id))
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
    # Optimize MongoDB storage periodically
    if USE_MONGO_FOR_AI and random.random() < 0.1:  # 10% chance to optimize on each message
        asyncio.create_task(mongo_db.optimize_conversation_storage(str(channel_id)))

    # The thread creation will be handled in the calling function
    return ai_response

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
