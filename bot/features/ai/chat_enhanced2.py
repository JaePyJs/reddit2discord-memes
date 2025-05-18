"""
Enhanced AI Chat Utilities - Part 2

This module contains additional utility functions for the AI chat feature,
focusing on message formatting and history management.
"""

import re
from typing import List, Dict, Any

# Constants
MAX_HISTORY_TOKENS = 4000  # Approximate token limit for history
MAX_MESSAGE_LENGTH = 2000  # Discord's message length limit

# Reference to the global message history
# This will be imported and used by the main chat module
message_history: Dict[int, List[Dict[str, Any]]] = {}

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
