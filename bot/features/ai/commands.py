import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
import re
from typing import Optional, Dict, Any
from bot.features.ai.chat import (
    set_ai_channel, is_ai_channel, get_ai_channel, get_ai_response,
    clear_chat_history, split_message, format_error_message, create_ai_response_embed,
    set_user_preference, get_user_preferences, should_create_thread, extract_thread_topic,
    create_thread_for_topic, handle_long_response, format_markdown, create_table_markdown
)
from bot.features.ai.context import (
    get_message_context, needs_context, is_asking_for_clarification,
    format_context_for_ai, get_cached_context
)
from bot.core.config import OPENROUTER_API_KEY, USE_MONGO_FOR_AI

# Import MongoDB utilities if enabled
if USE_MONGO_FOR_AI:
    from bot.utils import mongo_db

class AICommands(commands.Cog):
    """AI chat commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Event handler for incoming messages to process AI chat responses.
        Responds in:
        1. Designated AI chat channels
        2. Direct Messages (DMs)
        3. When the bot is mentioned in any channel
        """
        # Ignore messages from bots (including self) to prevent loops
        if message.author.bot:
            return

        # Check if this is a DM
        if not message.guild:
            # This is a DM - create a unique channel ID for this conversation
            dm_channel_id = f"dm_{message.author.id}"

            # Get the message content
            content = message.content.strip()

            # Check for image attachments
            image_urls = []
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    image_urls.append(attachment.url)

            # Skip empty messages with no attachments or those that appear to be commands
            if (not content and not image_urls) or content.startswith('/'):
                return

            # Special commands to clear history
            if content.lower() in ['clear history', 'reset conversation', 'reset', 'start over', 'clear chat']:
                if clear_chat_history(dm_channel_id):
                    await message.channel.send("✅ Chat history cleared. Starting fresh!")
                else:
                    await message.channel.send("No chat history to clear!")
                return

            # Send typing indicator to show the bot is processing
            async with message.channel.typing():
                thinking_emoji = "🤔"
                try:
                    # Show "thinking" reaction
                    await message.add_reaction(thinking_emoji)

                    # Get AI response with a casual, best-friend-like system prompt for DMs
                    system_prompt = (
                        f"You are Nite, {message.author.display_name}'s best friend chatting in private Discord DMs. "
                        f"Your personality is casual, warm, and authentic. "
                        f"Talk like you've known each other for years - use casual language, slang, abbreviations, and the occasional typo to sound natural. "
                        f"Be conversational and genuine, not formal or robotic. "
                        f"Use emojis naturally like a real person would in chat. "
                        f"Keep your tone supportive, honest, and occasionally playful or sarcastic when appropriate. "
                        f"You can disagree respectfully when you think your friend is wrong - real friends don't just agree with everything. "
                        f"When mentioning a user, simply use their name without any special formatting. "
                        f"If you don't know something, just admit it casually instead of being apologetic. "
                        f"Remember details about {message.author.display_name} from previous messages when relevant. "
                        f"Occasionally ask follow-up questions to show you're engaged in the conversation. "
                        f"Since this is a private DM, you can be more detailed and personal in your responses. "
                        f"If the user sends an image, describe what you see in a natural way, as if you're just chatting with a friend who shared a photo. "
                        f"Comment on images casually like 'Oh cool pic!' or 'Nice photo!' followed by observations about what you see. "
                        f"You can use Discord's markdown formatting in your responses: **bold** for emphasis, *italics* for subtle emphasis, and ```code blocks``` for code or technical information. "
                        f"For complex topics, you can create a thread by detecting when someone types !thread or asks a complex question. "
                        f"You can also respond to natural language commands like 'delete the last 5 messages' if the user has appropriate permissions. "
                        f"IMPORTANT: Your responses should NOT be structured like an AI assistant - no formal introductions, no 'I'd be happy to help' phrases, and no summarizing at the end."
                    )

                    # Pass username, user ID, image URLs, and original message for advanced features
                    response = await get_ai_response(
                        content,
                        dm_channel_id,
                        system_prompt,
                        message.author.display_name,
                        str(message.author.id),
                        image_urls,
                        message
                    )

                    # Remove thinking reaction
                    await message.remove_reaction(thinking_emoji, self.bot.user)

                    # Add checkmark reaction to show successful response
                    await message.add_reaction("✅")

                    # Handle different response types
                    if isinstance(response, tuple):
                        # This is a tuple of (message_parts, file_attachment)
                        response_parts, file_attachment = response

                        # Send the first part as a reply
                        await message.reply(
                            response_parts[0],
                            mention_author=True,
                            files=[file_attachment] if file_attachment else None
                        )

                        # Send remaining parts as follow-ups
                        for part in response_parts[1:]:
                            await message.channel.send(part)
                    else:
                        # This is a simple string response
                        # Split response if too long for a single message
                        response_parts = split_message(response)

                        # Send the first part as a reply
                        await message.reply(response_parts[0], mention_author=True)

                        # Send remaining parts as follow-ups
                        for part in response_parts[1:]:
                            await message.channel.send(part)

                except Exception as e:
                    # Remove thinking reaction
                    try:
                        await message.remove_reaction(thinking_emoji, self.bot.user)
                    except:
                        pass

                    # Add error reaction
                    await message.add_reaction("❌")

                    # Format and send error message
                    error_message = format_error_message(str(e))
                    await message.reply(error_message)

            return

        # Get guild and channel IDs
        guild_id = message.guild.id
        channel_id = message.channel.id

        # Check if this is the designated AI chat channel
        is_designated_channel = is_ai_channel(guild_id, channel_id)

        # Check if the bot is mentioned
        is_mentioned = self.bot.user in message.mentions

        # Only proceed if this is an AI channel or the bot is mentioned
        if not (is_designated_channel or is_mentioned):
            return

        # Get the message content
        content = message.content.strip()

        # If this is a mention, remove the mention from the content
        if is_mentioned:
            # Extract content without the mention
            content = re.sub(r'<@!?[0-9]+>', '', content).strip()

            # If there's no content after removing the mention, provide a helpful response
            if not content:
                await message.reply("Hi there! You can ask me anything or chat with me by mentioning me.")
                return

        # Check for image attachments
        image_urls = []
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                image_urls.append(attachment.url)

        # Skip empty messages with no attachments or those that appear to be commands
        if (not content and not image_urls) or (content.startswith('/') and not is_mentioned):
            return

        # Special commands to clear history
        if content.lower() in ['clear history', 'reset conversation', 'reset', 'start over', 'clear chat']:
            # For mentions, create a special channel ID
            if is_mentioned and not is_designated_channel:
                mention_channel_id = f"mention_{channel_id}_{message.author.id}"
                if clear_chat_history(mention_channel_id):
                    await message.reply("✅ Chat history cleared. Starting fresh!")
                else:
                    await message.reply("No chat history to clear!")
            else:
                if clear_chat_history(channel_id):
                    await message.reply("✅ Chat history cleared. Starting fresh!")
                else:
                    await message.reply("No chat history to clear!")
            return

        # Send typing indicator to show the bot is processing
        async with message.channel.typing():
            thinking_emoji = "🤔"
            try:
                # Show "thinking" reaction
                await message.add_reaction(thinking_emoji)

                # Get user preferences if available
                preferences = await get_user_preferences(str(message.author.id))

                # Get user preferences (these will be used in future enhancements)
                # Currently using default system prompt regardless of preferences
                _ = preferences.get("tone", "neutral")
                _ = preferences.get("emoji_level", "moderate")
                _ = preferences.get("use_name", True)

                # Get guild configuration for context awareness
                guild_config = None
                if USE_MONGO_FOR_AI:
                    guild_config = await mongo_db.get_guild_config(guild_id)

                # Get context settings
                max_context_messages = 5  # Default
                enable_context_awareness = True  # Default

                if guild_config and "bot_config" in guild_config:
                    bot_config = guild_config.get("bot_config", {})
                    max_context_messages = bot_config.get("max_context_messages", 5)
                    enable_context_awareness = bot_config.get("enable_context_awareness", True)

                # Initialize context string
                context_str = ""

                # For mentions, create a special channel ID
                if is_mentioned and not is_designated_channel:
                    channel_id = f"mention_{channel_id}_{message.author.id}"

                    # Check if the message likely needs context
                    if enable_context_awareness and needs_context(content):
                        # Get previous messages for context
                        context_messages = await get_message_context(
                            message.channel,
                            message,
                            max_messages=max_context_messages
                        )

                        # Format context for the AI
                        if context_messages:
                            context_str = await format_context_for_ai(context_messages)

                # Build a system prompt for a super casual, best-friend-like chat
                system_prompt = (
                    f"You are Nite, everyone's best friend chatting on Discord. Your personality is casual, warm, and authentic. "
                    f"Talk to people like you've known them for years. "
                    f"Use casual language, slang, abbreviations, and the occasional typo to sound natural. "
                    f"Don't be overly formal or robotic - be conversational and genuine. "
                    f"Use emojis naturally like a real person would in chat. "
                    f"Keep your tone supportive, honest, and occasionally playful or sarcastic when appropriate. "
                    f"You can disagree respectfully when you think someone is wrong - real friends don't just agree with everything. "
                    f"If you don't know something, just admit it casually instead of being apologetic. "
                    f"When mentioning a user, use @username to properly mention them or simply use their name without any special formatting. "
                    f"IMPORTANT: Never use square brackets around usernames like [username] and don't add commas after mentions. "
                    f"Remember details about people from previous messages when relevant. "
                    f"Occasionally ask follow-up questions to show you're engaged in the conversation. "
                    f"If someone sends an image, describe what you see in a natural way, as if you're just chatting with a friend who shared a photo. "
                    f"Comment on images casually like 'Oh cool pic!' or 'Nice photo!' followed by observations about what you see. "
                    f"This is a group chat where multiple users might be talking. Pay attention to usernames to know who's talking. "
                    f"When multiple people are chatting, make sure to address the specific person you're responding to by using their name or by @mentioning them. "
                    f"Always respond to the most recent message in the conversation, which is from {message.author.display_name}. "
                    f"If someone asks about an image that was shared earlier, describe what was in that image based on your previous responses. "
                    f"You can use Discord's markdown formatting in your responses: **bold** for emphasis, *italics* for subtle emphasis, and ```code blocks``` for code or technical information. "
                    f"For complex topics, you can create a thread by detecting when someone types !thread or asks a complex question. "
                    f"You can also respond to natural language commands like 'delete the last 5 messages' if the user has appropriate permissions. "
                    f"If you're unsure what the user is referring to, politely ask for clarification. "
                    f"IMPORTANT: Your responses should NOT be structured like an AI assistant - no formal introductions, no 'I'd be happy to help' phrases, and no summarizing at the end."
                )

                # If we have context, add it to the prompt
                if context_str:
                    prompt = f"{context_str}Now responding to: {content}"
                else:
                    prompt = content

                # Pass username, user ID, image URLs, and original message for advanced features
                response = await get_ai_response(
                    prompt,
                    channel_id,
                    system_prompt,
                    message.author.display_name,
                    str(message.author.id),
                    image_urls,
                    message
                )

                # Remove thinking reaction
                await message.remove_reaction(thinking_emoji, self.bot.user)

                # Add checkmark reaction to show successful response
                await message.add_reaction("✅")

                # Check if we should create a thread for this conversation
                create_thread = should_create_thread(content)
                thread = None

                # Handle different response types
                if isinstance(response, tuple):
                    # This is a tuple of (message_parts, file_attachment)
                    response_parts, file_attachment = response

                    # Send the first part as a reply
                    reply_message = await message.reply(
                        response_parts[0],
                        mention_author=True,
                        files=[file_attachment] if file_attachment else None
                    )

                    # If we need to create a thread, do it with the first message
                    if create_thread and not is_mentioned:
                        thread_topic = extract_thread_topic(content)
                        thread = await create_thread_for_topic(reply_message, thread_topic)

                    # Send remaining parts as follow-ups
                    for part in response_parts[1:]:
                        if thread:
                            await thread.send(part)
                        else:
                            await message.channel.send(part)
                else:
                    # This is a simple string response
                    # Split response if too long for a single message
                    response_parts = split_message(response)

                    # Send the first part as a reply
                    reply_message = await message.reply(response_parts[0], mention_author=True)

                    # If we need to create a thread, do it with the reply message
                    if create_thread and not is_mentioned:
                        thread_topic = extract_thread_topic(content)
                        thread = await create_thread_for_topic(reply_message, thread_topic)

                        # Send a welcome message in the thread
                        if thread:
                            await thread.send(f"I've created this thread to discuss: **{thread_topic}**\nFeel free to continue the conversation here!")

                    # Send remaining parts as follow-ups
                    for part in response_parts[1:]:
                        if thread:
                            await thread.send(part)
                        else:
                            await message.channel.send(part)

            except Exception as e:
                # Remove thinking reaction
                try:
                    await message.remove_reaction(thinking_emoji, self.bot.user)
                except:
                    pass

                # Add error reaction
                await message.add_reaction("❌")

                # Format and send error message
                error_message = format_error_message(str(e))
                await message.reply(error_message)

    @app_commands.command(
        name='ai_chat_set',
        description='Set the current channel as the AI chatbot channel'
    )
    async def ai_chat_set(self, interaction: discord.Interaction):
        """Set the current channel as the dedicated AI chatbot channel"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not interaction.channel.permissions_for(interaction.user).manage_channels:
            await interaction.response.send_message(
                "You need 'Manage Channels' permission to set the AI chat channel.",
                ephemeral=True
            )
            return

        # Set the channel
        _, previous_channel_id = set_ai_channel(interaction.guild.id, interaction.channel.id)

        # Get previous channel mention if it exists
        previous_channel_mention = None
        if previous_channel_id:
            previous_channel = interaction.guild.get_channel(previous_channel_id)
            if previous_channel:
                previous_channel_mention = previous_channel.mention

        # Create confirmation embed
        embed = discord.Embed(
            title="AI Chat Channel Set",
            description=f"This channel is now set as the AI chat channel for {interaction.guild.name}.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="How to use",
            value="Just send any message in this channel to get a response from the AI assistant.",
            inline=False
        )

        embed.add_field(
            name="Managing History",
            value=(
                "Use `/clear_chat` to clear all conversation history.\n"
                "Use `/clear_chat count:5` to clear only the 5 most recent messages.\n"
                "Use `/delete_messages count:10` to delete actual messages in the channel (requires Manage Messages permission)."
            ),
            inline=False
        )

        if previous_channel_mention:
            embed.add_field(
                name="Note",
                value=f"AI chat has been **deactivated** in {previous_channel_mention} and moved to this channel.",
                inline=False
            )

        embed.set_footer(text="AI Model: meta-llama/llama-4-maverick")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='clear_chat',
        description='Clear AI chat history'
    )
    @app_commands.describe(
        count='Number of recent messages to clear (leave empty to clear all)'
    )
    async def clear_chat(self, interaction: discord.Interaction, count: Optional[int] = None):
        """Clear the AI chat history for the current channel"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        channel_id = interaction.channel.id

        # Check if this is the AI chat channel
        if not is_ai_channel(guild_id, channel_id):
            await interaction.response.send_message(
                "This command can only be used in the designated AI chat channel.",
                ephemeral=True
            )
            return

        # Validate count if provided
        if count is not None:
            if count <= 0:
                await interaction.response.send_message("Count must be a positive number.", ephemeral=True)
                return

        # Clear history
        if clear_chat_history(channel_id, count):
            if count:
                await interaction.response.send_message(f"Cleared the {count} most recent messages from AI chat history.")
            else:
                await interaction.response.send_message("Cleared all AI chat history. Starting fresh!")
        else:
            await interaction.response.send_message("No chat history to clear!", ephemeral=True)

    @app_commands.command(
        name='set_context_depth',
        description='Set how many previous messages the bot checks for context'
    )
    @app_commands.describe(
        depth='Number of previous messages to check (1-10)'
    )
    async def set_context_depth(self, interaction: discord.Interaction, depth: int):
        """Set the number of previous messages to check for context"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need 'Manage Server' permission to change bot configuration.",
                ephemeral=True
            )
            return

        # Validate depth
        if depth < 1 or depth > 10:
            await interaction.response.send_message(
                "Context depth must be between 1 and 10 messages.",
                ephemeral=True
            )
            return

        # Update configuration
        if USE_MONGO_FOR_AI:
            try:
                await mongo_db.update_guild_config(
                    interaction.guild.id,
                    "bot_config.max_context_messages",
                    depth
                )
            except Exception as e:
                logging.error(f"Error updating guild configuration: {e}")
                await interaction.response.send_message(
                    f"Error updating configuration: {str(e)}",
                    ephemeral=True
                )
                return

        # Confirm the change
        await interaction.response.send_message(
            f"Context depth set to {depth} messages. When mentioned, I'll check up to {depth} previous messages for context.",
            ephemeral=False
        )

    @app_commands.command(
        name='toggle_context_awareness',
        description='Enable or disable context awareness for mentions'
    )
    async def toggle_context_awareness(self, interaction: discord.Interaction):
        """Toggle whether the bot uses context awareness when mentioned"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need 'Manage Server' permission to change bot configuration.",
                ephemeral=True
            )
            return

        # Get current setting
        current_setting = True  # Default
        if USE_MONGO_FOR_AI:
            try:
                guild_config = await mongo_db.get_guild_config(interaction.guild.id)
                if guild_config and "bot_config" in guild_config:
                    current_setting = guild_config["bot_config"].get("enable_context_awareness", True)
            except Exception as e:
                logging.error(f"Error getting guild configuration: {e}")

        # Toggle the setting
        new_setting = not current_setting

        # Update configuration
        if USE_MONGO_FOR_AI:
            try:
                await mongo_db.update_guild_config(
                    interaction.guild.id,
                    "bot_config.enable_context_awareness",
                    new_setting
                )
            except Exception as e:
                logging.error(f"Error updating guild configuration: {e}")
                await interaction.response.send_message(
                    f"Error updating configuration: {str(e)}",
                    ephemeral=True
                )
                return

        # Confirm the change
        status = "enabled" if new_setting else "disabled"
        await interaction.response.send_message(
            f"Context awareness is now {status}. When mentioned, I'll " +
            ("check previous messages for context." if new_setting else "no longer check previous messages for context."),
            ephemeral=False
        )

    @app_commands.command(
        name='clear_all_history',
        description='Clear all AI chat history from the database (admin only)'
    )
    async def clear_all_history(self, interaction: discord.Interaction):
        """Clear all AI chat history from the database"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check permissions - require administrator
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You need 'Administrator' permission to clear all chat history.",
                ephemeral=True
            )
            return

        # Defer the response since this might take a while
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Clear all chat history
        if USE_MONGO_FOR_AI:
            try:
                # Clear all conversations
                await mongo_db.clear_all_conversations()
                await interaction.followup.send("✅ All AI chat history has been cleared from the database.", ephemeral=True)
            except Exception as e:
                logging.error(f"Error clearing chat history: {e}")
                await interaction.followup.send(f"Error clearing chat history: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send("MongoDB is not enabled. Cannot clear chat history.", ephemeral=True)

    @app_commands.command(
        name='ai_chat_help',
        description='Get help with using the AI chatbot'
    )
    async def ai_chat_help(self, interaction: discord.Interaction):
        """Display help information for the AI chatbot"""
        embed = discord.Embed(
            title="AI Chatbot Help",
            description="This bot includes an AI chatbot powered by Llama 4 Maverick via OpenRouter.",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Setting Up",
            value=(
                "Use `/ai_chat_set` in a channel to designate it as the AI chat channel.\n"
                "Only users with 'Manage Channels' permission can set the AI chat channel."
            ),
            inline=False
        )

        embed.add_field(
            name="Having a Conversation",
            value=(
                "Simply send messages in the designated AI chat channel to talk with the AI.\n"
                "You can also send images, and the AI will describe and comment on them!\n"
                "The bot will respond to all messages in that channel that aren't commands.\n"
                "You can also mention the bot in any channel to chat with it!\n"
                "For complex topics, the bot can create threads to keep conversations organized."
            ),
            inline=False
        )

        embed.add_field(
            name="Context Awareness",
            value=(
                "When you mention the bot with references like 'this' or 'that', it will check previous messages for context.\n"
                "Use `/set_context_depth` to set how many previous messages the bot checks (1-10).\n"
                "Use `/toggle_context_awareness` to enable or disable this feature."
            ),
            inline=False
        )

        embed.add_field(
            name="Managing History",
            value=(
                "Use `/clear_chat` to clear all conversation history.\n"
                "Use `/clear_chat count:5` to clear only the 5 most recent messages.\n"
                "Type `reset` or `clear history` in the chat to quickly reset the conversation.\n"
                "Use `/delete_messages count:10` to delete actual messages in the channel (requires Manage Messages permission)."
            ),
            inline=False
        )

        embed.add_field(
            name="Special Features",
            value=(
                "• **Thread Creation**: Type `!thread` or ask a complex question to create a new thread.\n"
                "• **Markdown Formatting**: The AI can format responses with bold, italics, and code blocks.\n"
                "• **Long Responses**: For very long responses, the AI will create a text file attachment.\n"
                "• **Natural Commands**: Ask the AI to 'delete the last 5 messages' (requires permissions).\n"
                "• **User Mentions**: The AI can mention users directly in responses when appropriate."
            ),
            inline=False
        )

        embed.add_field(
            name="Limitations",
            value=(
                "• The AI can only 'remember' a limited amount of conversation history.\n"
                "• Very long conversations may require clearing the history.\n"
                "• The AI operates independently of the meme bot's other functions."
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name='delete_messages',
        description='Delete a specified number of messages in the AI chat channel'
    )
    @app_commands.describe(
        count='Number of messages to delete (up to 100 at a time)'
    )
    async def delete_messages(self, interaction: discord.Interaction, count: int = 10):
        """Delete a specified number of messages in the channel"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message(
                "You need 'Manage Messages' permission to delete messages.",
                ephemeral=True
            )
            return

        # Validate count
        if count <= 0:
            await interaction.response.send_message("Count must be a positive number.", ephemeral=True)
            return

        if count > 100:
            await interaction.response.send_message(
                "You can only delete up to 100 messages at a time.",
                ephemeral=True
            )
            return

        # Defer the response since this might take a moment
        await interaction.response.defer(ephemeral=True)

        try:
            # Delete messages
            deleted = await interaction.channel.purge(limit=count)

            # Send confirmation
            await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to delete messages in this channel.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"An error occurred while deleting messages: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name='dm_chat',
        description='Start a private conversation with the AI in your DMs'
    )
    async def dm_chat(self, interaction: discord.Interaction):
        """Start a private DM conversation with the AI"""
        # Defer the response since this might take a moment
        await interaction.response.defer(ephemeral=True)

        try:
            # Try to send a DM to the user
            dm_channel = await interaction.user.create_dm()

            # Send a casual welcome message instead of an embed
            welcome_message = (
                f"Hey {interaction.user.display_name}! 👋 What's up? I'm Nite, your Discord buddy!\n\n"
                f"We can chat about anything here - just like texting a friend. Your messages stay between us, and I'll remember our conversations.\n\n"
                f"You can even send me images, and I'll tell you what I see in them! 📸\n\n"
                f"I can use **bold text**, *italics*, and ```code blocks``` to make my messages more readable.\n\n"
                f"For complex topics, just type !thread and I'll create a thread to keep our conversation organized.\n\n"
                f"If you ever wanna start fresh, just type 'reset' or 'clear history' and we'll start over.\n\n"
                f"So... what's on your mind today? 😊"
            )

            await dm_channel.send(welcome_message)

            # Send confirmation to the user in the server
            await interaction.followup.send(
                "I've sent you a DM! Check your direct messages to start our conversation.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Please make sure you have DMs enabled for this server.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name='ai_preferences',
        description='Set your personal preferences for AI chat interactions'
    )
    @app_commands.describe(
        tone='Communication style preference',
        emoji_level='How many emojis to use in responses',
        use_name='Whether the AI should address you by name'
    )
    async def ai_preferences(
        self,
        interaction: discord.Interaction,
        tone: Optional[str] = None,
        emoji_level: Optional[str] = None,
        use_name: Optional[bool] = None
    ):
        """Set personal preferences for AI chat interactions"""
        # Validate tone
        valid_tones = ["super_casual", "casual", "neutral", "formal"]
        if tone is not None and tone not in valid_tones:
            await interaction.response.send_message(
                f"Invalid tone. Please choose from: {', '.join(valid_tones)}",
                ephemeral=True
            )
            return

        # Validate emoji level
        valid_emoji_levels = ["none", "minimal", "moderate", "abundant"]
        if emoji_level is not None and emoji_level not in valid_emoji_levels:
            await interaction.response.send_message(
                f"Invalid emoji level. Please choose from: {', '.join(valid_emoji_levels)}",
                ephemeral=True
            )
            return

        # Defer response since this might take a moment
        await interaction.response.defer(ephemeral=True)

        # Update preferences
        updated = False
        if tone is not None:
            updated = await set_user_preference(str(interaction.user.id), "tone", tone) or updated

        if emoji_level is not None:
            updated = await set_user_preference(str(interaction.user.id), "emoji_level", emoji_level) or updated

        if use_name is not None:
            updated = await set_user_preference(str(interaction.user.id), "use_name", use_name) or updated

        if updated:
            # Get current preferences to show the user
            preferences = await get_user_preferences(str(interaction.user.id))

            # Create confirmation embed
            embed = discord.Embed(
                title="AI Chat Preferences Updated",
                description="Your AI chat preferences have been updated.",
                color=discord.Color.green()
            )

            # Add fields for each preference
            embed.add_field(
                name="Tone",
                value=preferences.get("tone", "neutral").replace("_", " ").title(),
                inline=True
            )

            embed.add_field(
                name="Emoji Usage",
                value=preferences.get("emoji_level", "moderate").title(),
                inline=True
            )

            embed.add_field(
                name="Address by Name",
                value="Yes" if preferences.get("use_name", True) else "No",
                inline=True
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                "No preferences were updated. Please specify at least one preference to change.",
                ephemeral=True
            )

    @app_commands.command(
        name='ai_preferences_view',
        description='View your current AI chat preferences'
    )
    async def ai_preferences_view(self, interaction: discord.Interaction):
        """View current AI chat preferences"""
        # Defer response since this might take a moment
        await interaction.response.defer(ephemeral=True)

        # Get current preferences
        preferences = await get_user_preferences(str(interaction.user.id))

        # Create embed
        embed = discord.Embed(
            title="Your AI Chat Preferences",
            description="Here are your current AI chat preferences:",
            color=discord.Color.blue()
        )

        # Add fields for each preference
        embed.add_field(
            name="Tone",
            value=preferences.get("tone", "neutral").replace("_", " ").title(),
            inline=True
        )

        embed.add_field(
            name="Emoji Usage",
            value=preferences.get("emoji_level", "moderate").title(),
            inline=True
        )

        embed.add_field(
            name="Address by Name",
            value="Yes" if preferences.get("use_name", True) else "No",
            inline=True
        )

        embed.add_field(
            name="How to Change",
            value="Use `/ai_preferences` to update these settings.",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """Add the AI commands cog to the bot"""
    cog = AICommands(bot)
    await bot.add_cog(cog)
    print(f"Registered AI commands cog")
