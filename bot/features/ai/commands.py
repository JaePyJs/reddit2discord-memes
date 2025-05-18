import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import Optional
from bot.features.ai.chat import (
    set_ai_channel, is_ai_channel, get_ai_channel, get_ai_response, 
    clear_chat_history, split_message, format_error_message, create_ai_response_embed,
    set_user_preference, get_user_preferences
)
from bot.core.config import OPENROUTER_API_KEY

class AICommands(commands.Cog):
    """AI chat commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
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
        success, previous_channel_id = set_ai_channel(interaction.guild.id, interaction.channel.id)
        
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
                "The bot will respond to all messages in that channel that aren't commands."
            ),
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
            
            # Create welcome embed
            embed = discord.Embed(
                title="Private AI Chat",
                description=(
                    "Hello! I'm your AI assistant. You can chat with me here in private.\n\n"
                    "Just send any message to start a conversation!"
                ),
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Tips",
                value=(
                    "• Your conversation history is saved between sessions\n"
                    "• Type 'clear history' to start fresh\n"
                    "• I can help with questions, creative writing, and more"
                ),
                inline=False
            )
            
            embed.set_footer(text="Powered by Llama 4 Maverick")
            
            await dm_channel.send(embed=embed)
            
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
