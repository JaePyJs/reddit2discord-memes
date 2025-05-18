import discord
from discord import app_commands, Intents
from discord.ext import commands
import os
import logging
import asyncio
from bot.utils.config import DISCORD_TOKEN, DEFAULT_GUILD_ID, BOT_PREFIX, OPENROUTER_API_KEY
from bot.integrations.reddit import fetch_new_posts, fetch_random_best_post
from bot.utils.template_manager import TemplateManager
from bot.utils import db
from PIL import Image, ImageDraw
import io
import re
from bot.utils.text_utils import draw_wrapped_text
from bot.utils.font_utils import get_best_fit_font
from bot.utils.color_utils import get_average_luminance, pick_text_color
from bot.utils.autopost_store import load_store, save_store, add_subreddit, remove_subreddit, get_subreddits
from bot.utils.dependency_checker import verify_dependencies
from bot.integrations.ai_chat import (
    set_ai_channel, is_ai_channel, get_ai_channel, get_ai_response, 
    clear_chat_history, split_message, format_error_message, create_ai_response_embed,
    OpenRouterError, message_history
)
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Utility logging helpers
def log_command_registration(cmd_name):
    logging.info(f"Registered slash command: {cmd_name}")

def log_command_execution(cmd_name, interaction):
    user = getattr(interaction.user, 'id', 'unknown') if interaction else 'unknown'
    logging.info(f"Executed slash command: {cmd_name} by user {user}")

# Basic setup
intents = Intents.default()
intents.message_content = True
intents.guilds = True

# Check dependencies
verify_dependencies()

# Initialize database
db.init_db()
db.add_default_templates()
print("Database initialized with default templates")

# Create bot instance
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Event handler for AI chatbot
@bot.event
async def on_message(message: discord.Message):
    """
    Event handler for incoming messages to process AI chat responses.
    Only responds in the designated AI chat channel or in DMs.
    """
    # Ignore messages from bots (including self) to prevent loops
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if this is a DM
    if not message.guild:
        # This is a DM - create a unique channel ID for this conversation
        dm_channel_id = f"dm_{message.author.id}"
        
        # Get the message content
        content = message.content.strip()
        
        # Skip empty messages or those that appear to be commands
        if not content or content.startswith(BOT_PREFIX):
            return
        
        # Send typing indicator to show the bot is processing
        async with message.channel.typing():
            thinking_emoji = "🤔"
            try:
                # Show "thinking" reaction
                await message.add_reaction(thinking_emoji)
                
                # Get AI response - with an extremely informal best friend system prompt
                system_prompt = "You are Nite, the absolute BESTIE chatting in a private DM! 🤪 Talk super casually with tons of slang, emojis, and abbrevs like 'lol', 'omg', 'ngl', 'tbh', etc. Be playful, tease them (nicely!), share jokes, and stay hyped about whatever they're talking about! 💯 NEVER be formal or robotic - talk EXACTLY like a bestie texting. Your personality is warm, supportive but also witty and sometimes sarcastic in the most friendly way possible. This is a private one-on-one conversation! 🔥"
                
                # Pass username and user ID for better conversation tracking
                response = await get_ai_response(content, dm_channel_id, system_prompt, message.author.display_name, str(message.author.id))
                
                # Remove thinking reaction
                await message.remove_reaction(thinking_emoji, bot.user)
                
                # Split response if too long for a single message
                response_parts = split_message(response)
                
                # Add checkmark reaction to show successful response
                await message.add_reaction("✅")
                
                # Send response as regular message (embeds look weird in DMs)
                for part in response_parts:
                    await message.reply(part)
                
            except OpenRouterError as e:
                # Remove thinking reaction if it exists
                try:
                    await message.remove_reaction(thinking_emoji, bot.user)
                except (discord.NotFound, discord.Forbidden, AttributeError):
                    pass  # Ignore if reaction wasn't added or can't be removed
                
                # Add error reaction
                try:
                    await message.add_reaction("⚠️")
                except (discord.NotFound, discord.Forbidden):
                    pass  # Ignore if message was deleted or no permission
                
                # Send error message
                error_message = format_error_message(e)
                await message.channel.send(error_message)
                logging.error(f"AI chat error: {str(e)}")
            
            except Exception as e:
                # Handle any unexpected errors
                logging.error(f"Unexpected error in AI chat: {str(e)}", exc_info=True)
                
                # Remove thinking reaction if it exists
                try:
                    await message.remove_reaction(thinking_emoji, bot.user)
                except (discord.NotFound, discord.Forbidden, AttributeError):
                    pass  # Ignore if reaction wasn't added or can't be removed
                
                # Add error reaction
                try:
                    await message.add_reaction("❌")
                except (discord.NotFound, discord.Forbidden):
                    pass  # Ignore if message was deleted or no permission
                
                # Send generic error message
                await message.channel.send("❌ **An unexpected error occurred.** Please try again later.")
        
        return  # Return here so we don't process as a guild message
    
    # Only process in guild channels that are set as AI channels
    if not message.guild:
        return  # Skip DMs
    
    guild_id = message.guild.id
    channel_id = message.channel.id
    
    # Check if this is the designated AI chat channel
    if not is_ai_channel(guild_id, channel_id):
        return
    
    # Get the message content
    content = message.content.strip()
    
    # Skip empty messages or those that appear to be commands
    if not content or content.startswith(BOT_PREFIX):
        return
    
    # Send typing indicator to show the bot is processing
    async with message.channel.typing():
        thinking_emoji = "🤔"
        try:
            # Show "thinking" reaction
            await message.add_reaction(thinking_emoji)
              # Get AI response - with an extremely informal best friend system prompt
            system_prompt = "You are Nite, the absolute BESTIE of everyone on this Discord server! 🤪 Talk super casually with tons of slang, emojis, and abbrevs like 'lol', 'omg', 'ngl', 'tbh', etc. Be playful, tease people (nicely!), share jokes, and stay hyped about whatever they're talking about! 💯 NEVER be formal or robotic - talk EXACTLY like a bestie texting in a group chat. Remember who you're talking to and always use their name occasionally like 'OMG [name], that's wild!' or 'yo [name], check this out!' 👀 Your personality is warm, supportive but also witty and sometimes sarcastic in the most friendly way possible. If multiple people are chatting with you at once, make it super clear who you're responding to by using their name. Act like you're in a group chat with all your besties! 🔥"
            
            # Pass username and user ID for better conversation tracking
            response = await get_ai_response(content, channel_id, system_prompt, message.author.display_name, str(message.author.id))
            
            # Remove thinking reaction
            await message.remove_reaction(thinking_emoji, bot.user)
            
            # Split response if too long for a single message
            response_parts = split_message(response)
            
            # Add checkmark reaction to show successful response
            await message.add_reaction("✅")
              # Send response as embed for better formatting, with reply to original message
            for part in response_parts:
                embed = create_ai_response_embed(part, message.author.display_name)
                # Use reply feature to clearly indicate who the AI is responding to
                await message.reply(embed=embed, mention_author=True)
            
        except OpenRouterError as e:
            # Remove thinking reaction if it exists
            try:
                await message.remove_reaction(thinking_emoji, bot.user)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                pass  # Ignore if reaction wasn't added or can't be removed
            
            # Add error reaction
            try:
                await message.add_reaction("⚠️")
            except (discord.NotFound, discord.Forbidden):
                pass  # Ignore if message was deleted or no permission
            
            # Send error message
            error_message = format_error_message(e)
            await message.channel.send(error_message)
            logging.error(f"AI chat error: {str(e)}")
        
        except Exception as e:
            # Handle any unexpected errors
            logging.error(f"Unexpected error in AI chat: {str(e)}", exc_info=True)
            
            # Remove thinking reaction if it exists
            try:
                await message.remove_reaction(thinking_emoji, bot.user)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                pass  # Ignore if reaction wasn't added or can't be removed
            
            # Add error reaction
            try:
                await message.add_reaction("❌")
            except (discord.NotFound, discord.Forbidden):
                pass  # Ignore if message was deleted or no permission
            
            # Send generic error message
            await message.channel.send("❌ **An unexpected error occurred.** Please try again later.")

# Simple test command
@bot.tree.command(name='test', description='Test command')
async def test(interaction: discord.Interaction):
    context = "DM" if interaction.guild is None else f"guild {interaction.guild.name}"
    await interaction.response.send_message(f'Test command works! This is a {context}.')

# --- Reddit Auto-Post Infrastructure ---
autopost_store = load_store()

# Background task to poll enabled subreddits and post new content
async def autopost_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            for guild_id, sub_map in list(autopost_store.items()):
                guild = bot.get_guild(int(guild_id))
                if guild is None:
                    continue
                for sub_name, cfg in sub_map.items():
                    channel = bot.get_channel(cfg['channel_id'])
                    if channel is None:
                        continue
                    last_id = cfg.get('last_posted_id')
                    last_ts = cfg.get('last_post_ts', 0)
                    now_ts = discord.utils.utcnow().timestamp()

                    # NEWEST flow
                    if now_ts - last_ts >= 300:
                        posts = fetch_new_posts(sub_name, limit=10)
                        if posts:
                            new_posts = []
                            for p in posts:
                                if p['id'] == last_id or p['id'] in cfg.get('seen_ids', []):
                                    continue  # Skip this post but check the next ones
                                new_posts.append(p)
                            if new_posts:
                                newest_post = new_posts[0]
                                await send_reddit_embed(channel, sub_name, newest_post, indicator="NEW")
                                cfg.setdefault('seen_ids', []).append(newest_post['id'])
                                cfg['last_posted_id'] = newest_post['id']
                                cfg['last_post_ts'] = now_ts

                    # BEST flow
                    last_best_ts = cfg.get('last_best_post_ts', 0)
                    if now_ts - last_best_ts >= 300:
                        best_post = fetch_random_best_post(sub_name, limit=100)
                        if best_post and best_post['id'] not in cfg.get('seen_ids', []):
                            await send_reddit_embed(channel, sub_name, best_post, indicator="BEST")
                            cfg.setdefault('seen_ids', []).append(best_post['id'])
                            cfg['last_best_post_ts'] = now_ts
                    
            # Save changes
            save_store(autopost_store)
        except Exception as e:
            logging.error(f"Autopost error: {e}")

        # Wait 30s before checking again
        await asyncio.sleep(30)

def send_reddit_embed(channel, sub_name, post, indicator="NEW"):
    logging.info(f"Sending {indicator} post from r/{sub_name} to channel {channel.id}")
    title = post['title']
    url = post['url']
    permalink = post['permalink']
    author = post['author']
    upvotes = post['score']
    comments = post['num_comments']
    
    try:
        embed = discord.Embed(
            title=f"{title}",
            url=f"https://reddit.com{permalink}",
            color=discord.Color.orange() if indicator == "NEW" else discord.Color.purple()
        )
        
        # Add image if it's a direct image link
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            embed.set_image(url=url)
        
        embed.add_field(name="Author", value=f"u/{author}", inline=True)
        embed.add_field(name="Upvotes", value=f"{upvotes}", inline=True)
        embed.add_field(name="Comments", value=f"{comments}", inline=True)
        
        if not url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            embed.add_field(name="Link", value=f"[Click here]({url})", inline=False)
        
        embed.set_footer(text=f"{indicator} • {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC • r/{sub_name}")
        return channel.send(embed=embed)
    except Exception as e:
        logging.error(f"Error sending reddit embed: {e}")
        return channel.send(f"**r/{sub_name}** - {title} - <{url}>")

# --- Command: Auto-Post Setup ---
@bot.tree.command(
    name='autopost_enable',
    description='Enable automatic posting of new/best content from a subreddit'
)
@app_commands.describe(
    subreddit='Subreddit name (without r/)',
    channel='Channel to post content in (defaults to current channel)'
)
async def autopost_enable(
    interaction: discord.Interaction,
    subreddit: str,
    channel: Optional[discord.TextChannel] = None
):
    log_command_execution('autopost_enable', interaction)
    
    # Normalize subreddit (strip r/ if present)
    subreddit = subreddit.strip('r/')
    subreddit = subreddit.strip('/')
    
    # Validate input
    if not subreddit:
        await interaction.response.send_message('Please provide a valid subreddit name.', ephemeral=True)
        return
    
    # Ensure guild (no DM)
    if not interaction.guild:
        await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
        return
    
    # Ensure permissions
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message('You need the "Manage Server" permission to use this command.', ephemeral=True)
        return
    
    # Use current channel if none specified
    target_channel = channel or interaction.channel
    
    # Register in auto-post storage
    add_subreddit(interaction.guild.id, subreddit, target_channel.id)
    # Refresh in-memory store
    global autopost_store
    autopost_store = load_store()
    await interaction.response.send_message(f'Auto-post enabled for r/{subreddit} in {target_channel.mention}.', ephemeral=False)

class AutoPostListView(discord.ui.View):
    """Paginated list of subreddits with disable buttons and navigation."""

    PAGE_SIZE = 5

    def __init__(self, guild_id: int, subs: Dict[str, Dict[str, Any]]):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.sub_items: List[tuple[str, Dict[str, Any]]] = list(subs.items())  # [(sub, cfg)]
        self.page = 0
        self.total_pages = max(1, (len(self.sub_items) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.refresh_items()

    # ---------------- Helper methods -----------------
    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"Enabled Auto-Post Subreddits (Page {self.page+1}/{self.total_pages})",
            color=0x2ecc71,
        )
        start = self.page * self.PAGE_SIZE
        for sub, cfg in self.sub_items[start : start + self.PAGE_SIZE]:
            embed.add_field(name=f"r/{sub}", value=f"Channel: <#{cfg['channel_id']}>", inline=False)
        embed.set_footer(text="Use the navigation buttons to view more or disable.")
        return embed

    def refresh_items(self):
        # Clear existing dynamic items (keep persistent nav buttons?) – easiest: clear then rebuild
        for item in list(self.children):
            self.remove_item(item)

        # Add disable buttons for current page
        start = self.page * self.PAGE_SIZE
        for sub, _ in self.sub_items[start : start + self.PAGE_SIZE]:
            self.add_item(self._make_disable_button(sub))

        # Navigation buttons
        prev_disabled = self.page == 0
        next_disabled = self.page >= self.total_pages - 1
        self.add_item(self._make_nav_button("Prev", "prev", prev_disabled))
        self.add_item(self._make_nav_button("Next", "next", next_disabled))

    # ---------------- Button factories -----------------
    def _make_disable_button(self, subreddit: str) -> discord.ui.Button:
        async def disable_callback(interaction: discord.Interaction):
            if remove_subreddit(self.guild_id, subreddit):
                # Refresh in-memory store
                global autopost_store
                autopost_store = load_store()
                
                # Update the UI
                self.sub_items = [(s, c) for s, c in self.sub_items if s != subreddit]
                self.total_pages = max(1, (len(self.sub_items) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
                if self.page >= self.total_pages and self.page > 0:
                    self.page = self.total_pages - 1
                
                if not self.sub_items:  # No items left
                    await interaction.response.edit_message(
                        content="No more auto-posted subreddits enabled.",
                        embed=None,
                        view=None
                    )
                    self.stop()
                    return
                
                self.refresh_items()
                await interaction.response.edit_message(
                    embed=self.make_embed(),
                    view=self
                )
            else:
                await interaction.response.send_message(
                    f"Error disabling r/{subreddit}",
                    ephemeral=True
                )

        button = discord.ui.Button(
            label=f"Disable r/{subreddit}",
            style=discord.ButtonStyle.danger,
            custom_id=f"disable_{subreddit}"
        )
        button.callback = disable_callback
        return button

    def _make_nav_button(self, label: str, direction: str, disabled: bool) -> discord.ui.Button:
        async def nav_callback(interaction: discord.Interaction):
            if direction == "prev":
                self.page = max(0, self.page - 1)
            else:  # next
                self.page = min(self.total_pages - 1, self.page + 1)
            
            self.refresh_items()
            await interaction.response.edit_message(
                embed=self.make_embed(),
                view=self
            )

        button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=f"nav_{direction}",
            disabled=disabled
        )
        button.callback = nav_callback
        return button

@bot.tree.command(
    name='autopost_list',
    description='List all auto-posted subreddits for this server'
)
async def autopost_list(interaction: discord.Interaction):
    log_command_execution('autopost_list', interaction)
    
    # Ensure guild context
    if not interaction.guild:
        await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    subreddits = get_subreddits(guild_id)
    
    if not subreddits:
        await interaction.response.send_message('No auto-posted subreddits are enabled for this server.', ephemeral=True)
        return
    
    # Create paginated view
    view = AutoPostListView(guild_id, subreddits)
    
    # Send initial view
    await interaction.response.send_message(
        embed=view.make_embed(),
        view=view
    )

# AI Chat Commands
@bot.tree.command(
    name='ai_chat_set',
    description='Set the current channel as the AI chatbot channel'
)
async def ai_chat_set(interaction: discord.Interaction):
    """Set the current channel as the dedicated AI chatbot channel"""
    log_command_execution('ai_chat_set', interaction)
    
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
    
    guild_id = interaction.guild.id
    channel_id = interaction.channel.id
    
    # Check if there was a previous channel
    previous_channel_id = get_ai_channel(guild_id)
    if previous_channel_id:
        previous_channel = bot.get_channel(previous_channel_id)
        if previous_channel and previous_channel.id != channel_id:
            previous_channel_mention = previous_channel.mention
        else:
            previous_channel_mention = None
    else:
        previous_channel_mention = None
    
    # Set this channel as the AI chat channel
    await set_ai_channel(guild_id, channel_id)
    
    # Create an informative embed
    embed = discord.Embed(
        title="AI Chat Activated",
        description=f"This channel is now set as the AI chat channel for this server. Simply send messages here to talk with the AI assistant!",
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

@bot.tree.command(
    name='clear_chat',
    description='Clear AI chat history'
)
@app_commands.describe(
    count='Number of recent messages to clear (leave empty to clear all)'
)
async def clear_chat(interaction: discord.Interaction, count: Optional[int] = None):
    """Clear the AI chat history for the current channel"""
    log_command_execution('clear_chat', interaction)
    
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

@bot.tree.command(
    name='ai_chat_help',
    description='Get help with using the AI chatbot'
)
async def ai_chat_help(interaction: discord.Interaction):
    """Display help information for the AI chatbot"""
    log_command_execution('ai_chat_help', interaction)
    
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

@bot.tree.command(
    name='delete_messages',
    description='Delete a specified number of messages in the AI chat channel'
)
@app_commands.describe(
    count='Number of messages to delete (up to 100 at a time)'
)
async def delete_messages(interaction: discord.Interaction, count: int = 10):
    """Delete messages in the AI chat channel"""
    log_command_execution('delete_messages', interaction)
    
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
    
    # Check permissions
    if not interaction.channel.permissions_for(interaction.user).manage_messages and not interaction.channel.permissions_for(interaction.user).administrator:
        await interaction.response.send_message(
            "You need 'Manage Messages' or 'Administrator' permission to delete messages.", 
            ephemeral=True
        )
        return
    
    # Check bot permissions
    if not interaction.channel.permissions_for(interaction.guild.me).manage_messages:
        await interaction.response.send_message(
            "I don't have permission to delete messages in this channel. Please give me 'Manage Messages' permission.", 
            ephemeral=True
        )
        return
    
    # Validate count
    if count <= 0:
        await interaction.response.send_message("Count must be a positive number.", ephemeral=True)
        return
    
    if count > 100:
        count = 100  # Discord API limit
    
    # Acknowledge the command
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Delete messages
        deleted = await interaction.channel.purge(limit=count)
        
        # Send confirmation
        await interaction.followup.send(f"Successfully deleted {len(deleted)} messages.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
    except discord.HTTPException as e:
        if e.code == 50034:  # Message too old
            await interaction.followup.send("Some messages were too old to delete (older than 14 days).", ephemeral=True)
        else:
            await interaction.followup.send(f"Error deleting messages: {e}", ephemeral=True)

# Register AI Chat Commands
log_command_registration('ai_chat_set')
log_command_registration('clear_chat')
log_command_registration('ai_chat_help')
log_command_registration('delete_messages')
log_command_registration('dm_chat')

# User DMs
@bot.tree.command(
    name='dm_chat',
    description='Start a private conversation with Nite in your DMs'
)
async def dm_chat(interaction: discord.Interaction):
    """Start a private DM conversation with the AI"""
    log_command_execution('dm_chat', interaction)
    
    # Try to send a DM to the user
    try:
        system_prompt = "You are Nite, the user's super casual and fun bestfriend on Discord. Use very informal language with lots of slang, emojis, and occasionally abbreviations like 'lol', 'omg', 'ngl', etc. Feel free to tease users playfully, share jokes, and be enthusiastic. Never be formal or robotic - talk exactly like a bestfriend would in a chat. Remember you're in a private DM with just this one person. Your personality is warm, supportive but also witty and sometimes sarcastic in a friendly way."
        
        # Create a unique channel ID for this DM conversation (using user ID)
        dm_channel_id = f"dm_{interaction.user.id}"
        
        # Initialize or clear existing conversation history for this DM
        message_history[dm_channel_id] = []
        
        # Send initial message
        await interaction.user.send(f"Hey {interaction.user.display_name}! 👋 What's up? I'm Nite, your AI bestie! This is our private chat - you can talk to me about anything here! Just hit me up whenever! 🔥")
        
        # Let the user know in the server
        await interaction.response.send_message("I've sent you a DM! Check your messages to chat with me privately! 💬", ephemeral=True)
        
    except discord.Forbidden:
        # User has DMs closed
        await interaction.response.send_message("I couldn't send you a DM! Make sure you have DMs enabled for this server.", ephemeral=True)

async def load_extensions():
    """Load all extensions (cogs)"""
    # Load the music cog
    try:
        await bot.load_extension("bot.music.commands")
        print("Loaded music commands extension")
    except Exception as e:
        print(f"Failed to load music extension: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

    # Load extensions
    await load_extensions()

    # Sync guild commands first if a default guild is specified (appear instantly)
    if DEFAULT_GUILD_ID:
        guild = discord.Object(id=DEFAULT_GUILD_ID)
        guild_commands = await bot.tree.sync(guild=guild)
        print(f'Synced {len(guild_commands)} guild commands for guild {DEFAULT_GUILD_ID}')

    # Then sync global commands (take time to appear)
    global_commands = await bot.tree.sync()
    print(f'Synced {len(global_commands)} global commands')

    print('Bot is ready!')

    # Start the background auto-post loop
    bot.loop.create_task(autopost_loop())

# Run the bot
bot.run(DISCORD_TOKEN)
