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
        # Check if user has permission to manage messages
        if not message.author.guild_permissions.manage_messages:
            return True, "You don't have permission to delete messages."

        try:
            # Get the number of messages to delete
            count = int(delete_match.group(1))
            if count < 1 or count > 100:
                return True, "I can only delete between 1 and 100 messages at a time."

            # Delete the messages
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

    # Check if we should create a thread for this message
    create_thread = False
    thread_topic = None
    if original_message and should_create_thread(prompt):
        create_thread = True
        thread_topic = extract_thread_topic(prompt)

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
                        content = f"{msg.get('username')}, {content}"
                    else:
                        content = f"Different user, {content}"
                elif role == "user" and msg.get("username"):
                    # Also add username for the current user's past messages for consistency
                    content = f"{msg.get('username')}, {content}"

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
                            content = f"{msg.get('username')}, {content}"
                        else:
                            content = f"Different user, {content}"
                    elif role == "user" and msg.get("username"):
                        # Also add username for the current user's past messages for consistency
                        content = f"{msg.get('username')}, {content}"

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
                        content = f"{msg.get('username')}, {content}"
                    else:
                        content = f"Different user, {content}"
                elif role == "user" and msg.get("username"):
                    # Also add username for the current user's past messages for consistency
                    content = f"{msg.get('username')}, {content}"

                # Check if this message had an image
                if msg.get("had_image", False):
                    content = f"{content} [Shared an image]"

                messages.append({"role": role, "content": content})
