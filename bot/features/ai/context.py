"""
Context management for AI chat responses.

This module provides functions for retrieving and analyzing message context
to improve the relevance of AI responses, particularly for mention-based interactions.
"""

import re
import logging
import discord
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bot.core.config import USE_MONGO_FOR_AI

# Import MongoDB utilities if enabled
if USE_MONGO_FOR_AI:
    from bot.utils import mongo_db

# Simple in-memory cache for context
context_cache = {}
CONTEXT_CACHE_TTL = 60  # seconds
MAX_CONTEXT_TOKENS = 1000  # Approximate token limit for context

async def get_message_context(channel, message, max_messages=5):
    """
    Retrieve context from previous messages in the channel.
    
    Args:
        channel: The Discord channel
        message: The current message that mentioned the bot
        max_messages: Maximum number of previous messages to retrieve
        
    Returns:
        A list of previous messages with author and content
    """
    context_messages = []
    try:
        # Get messages before the current one, limited by max_messages
        async for msg in channel.history(limit=max_messages + 1, before=message):
            # Skip messages from the bot itself
            if msg.author.bot:
                continue
                
            # Add message to context
            context_messages.append({
                "author": msg.author.display_name,
                "content": msg.content,
                "has_attachments": bool(msg.attachments),
                "timestamp": msg.created_at.isoformat()
            })
            
            # Break if we've collected enough context
            if len(context_messages) >= max_messages:
                break
                
        # Reverse to get chronological order
        context_messages.reverse()
        return context_messages
    except Exception as e:
        logging.error(f"Error retrieving message context: {e}")
        return []

def needs_context(content):
    """
    Determine if a message likely needs context from previous messages.
    
    Args:
        content: The message content
        
    Returns:
        Boolean indicating if context is needed
    """
    # List of patterns that suggest the message is referring to something else
    reference_patterns = [
        r'\b(this|that|it|these|those)\b',
        r'\bthe (above|previous)\b',
        r'what (is|was) that\b',
        r'what (do|does) (that|this) mean\b',
        r'what (are|were) (they|those|these)\b',
        r'what (about|of) (it|that|this)\b',
        r'thoughts on (this|that)\b',
        r'what do you think\b',
        r'can you explain\b',
        r'tell me (about|more)\b',
        r'what\'s (this|that)\b',
        r'why (is|was) (it|this|that)\b',
        r'how (does|do) (it|this|that) work\b'
    ]
    
    # Check if any pattern matches
    for pattern in reference_patterns:
        if re.search(pattern, content.lower()):
            return True
            
    return False

def is_asking_for_clarification(response):
    """
    Determine if the AI response is asking for clarification.
    
    Args:
        response: The AI's response text
        
    Returns:
        Boolean indicating if the AI is asking for clarification
    """
    clarification_patterns = [
        r"(can you|could you) (please )?(clarify|explain|specify)",
        r"I('m| am) not sure what (you('re| are)|that) referring to",
        r"what (specifically|exactly) (are|do) you mean",
        r"can you (provide|give) (more|additional) (context|details|information)",
        r"which (specific|particular) (thing|item|post|message) are you referring to",
        r"I('m| am) not sure (which|what) '(this|that|it)' (refers|is referring) to"
    ]
    
    for pattern in clarification_patterns:
        if re.search(pattern, response.lower()):
            return True
            
    return False

async def get_cached_context(channel_id, message_id, max_messages, bot):
    """
    Get context from cache or retrieve it if not cached.
    
    Args:
        channel_id: Discord channel ID
        message_id: Discord message ID
        max_messages: Maximum number of messages to retrieve
        bot: Discord bot instance for channel access
        
    Returns:
        List of context messages
    """
    cache_key = f"{channel_id}_{max_messages}"
    
    # Check if we have a recent cache entry
    if cache_key in context_cache:
        cache_entry = context_cache[cache_key]
        # Check if cache is still valid
        if (datetime.now() - cache_entry["timestamp"]).total_seconds() < CONTEXT_CACHE_TTL:
            return cache_entry["context"]
    
    # Not in cache or expired, retrieve context
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return []
        
    try:
        message = await channel.fetch_message(int(message_id))
        if not message:
            return []
    except:
        return []
        
    context = await get_message_context(channel, message, max_messages)
    
    # Cache the result
    context_cache[cache_key] = {
        "context": context,
        "timestamp": datetime.now()
    }
    
    return context

async def format_context_for_ai(context_messages):
    """
    Format context messages for the AI prompt.
    
    Args:
        context_messages: List of context message dictionaries
        
    Returns:
        Formatted context string
    """
    if not context_messages:
        return ""
        
    context_str = "Here's some context from the recent conversation:\n\n"
    for i, msg in enumerate(context_messages):
        context_str += f"{msg['author']}: {msg['content']}"
        if msg.get('has_attachments', False):
            context_str += " [had attachments]"
        context_str += "\n"
    context_str += "\nThe user is likely referring to something in this context when they say things like 'this' or 'that'.\n\n"
    
    return truncate_context(context_str)

def truncate_context(context_str, max_tokens=MAX_CONTEXT_TOKENS):
    """
    Truncate context to stay within token limits.
    
    Args:
        context_str: The context string
        max_tokens: Maximum number of tokens allowed
        
    Returns:
        Truncated context string
    """
    # Simple heuristic: ~4 chars per token
    max_chars = max_tokens * 4
    
    if len(context_str) <= max_chars:
        return context_str
        
    # Truncate and add indicator
    return context_str[:max_chars] + "... [context truncated]"
