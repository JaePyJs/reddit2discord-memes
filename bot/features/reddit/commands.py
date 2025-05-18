import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import Optional, List, Dict, Any
from bot.features.reddit.reddit import fetch_new_posts, fetch_random_best_post
from bot.core.config import DEFAULT_GUILD_ID
from bot.utils.autopost_store import add_subreddit, remove_subreddit, get_subreddits

class RedditCommands(commands.Cog):
    """Reddit integration commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.autopost_store = {}
        self.bot.loop.create_task(self.autopost_loop())
        
    @app_commands.command(
        name='reddit_autopost',
        description='Enable automatic posting of new/best content from a subreddit'
    )
    @app_commands.describe(
        subreddit='Subreddit name (without r/)',
        channel='Channel to post content in (defaults to current channel)'
    )
    async def reddit_autopost(
        self, 
        interaction: discord.Interaction, 
        subreddit: str,
        channel: Optional[discord.TextChannel] = None
    ):
        """Enable automatic posting from a subreddit"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
            
        # Check permissions
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "You need 'Manage Channels' permission to set up auto-posting.", 
                ephemeral=True
            )
            return
            
        # Clean up subreddit name
        subreddit = subreddit.strip().lower()
        if subreddit.startswith('r/'):
            subreddit = subreddit[2:]
        if subreddit.startswith('/r/'):
            subreddit = subreddit[3:]
            
        # Validate subreddit name
        if not subreddit or '/' in subreddit:
            await interaction.response.send_message(
                "Please provide a valid subreddit name (e.g., 'memes' or 'dankmemes').", 
                ephemeral=True
            )
            return
            
        # Use current channel if none specified
        target_channel = channel or interaction.channel
        
        # Add to auto-post configuration
        add_subreddit(interaction.guild.id, subreddit, target_channel.id)
        
        # Load the updated store
        self.autopost_store = get_subreddits(interaction.guild.id)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="Reddit Auto-Post Enabled",
            description=f"I'll automatically post new content from r/{subreddit} in {target_channel.mention}.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="What to Expect",
            value=(
                "• New posts will be shared approximately every 5 minutes\n"
                "• Best posts will be shared occasionally\n"
                "• Only image posts will be shared\n"
                "• Duplicate posts will be skipped"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Management",
            value="Use `/reddit_autopost_list` to view and manage your auto-post settings.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(
        name='reddit_autopost_list',
        description='List all subreddits configured for auto-posting'
    )
    async def reddit_autopost_list(self, interaction: discord.Interaction, page: int = 1):
        """List all subreddits configured for auto-posting"""
        # Ensure we're in a guild
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
            
        # Get subreddits for this guild
        subreddits = get_subreddits(interaction.guild.id)
        
        if not subreddits:
            await interaction.response.send_message(
                "No subreddits are currently configured for auto-posting in this server.", 
                ephemeral=True
            )
            return
            
        # Paginate the list (5 per page)
        items_per_page = 5
        sub_list = list(subreddits.items())
        max_pages = (len(sub_list) + items_per_page - 1) // items_per_page
        
        # Validate page number
        if page < 1:
            page = 1
        elif page > max_pages:
            page = max_pages
            
        # Get items for current page
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(sub_list))
        current_page_items = sub_list[start_idx:end_idx]
        
        # Create embed
        embed = discord.Embed(
            title="Reddit Auto-Post Configuration",
            description=f"Page {page}/{max_pages} • {len(sub_list)} subreddit(s) configured",
            color=discord.Color.blue()
        )
        
        # Add each subreddit to the embed
        for i, (sub_name, cfg) in enumerate(current_page_items, start=1):
            channel = interaction.guild.get_channel(cfg['channel_id'])
            channel_mention = channel.mention if channel else "Unknown Channel"
            
            embed.add_field(
                name=f"{i}. r/{sub_name}",
                value=f"Posts to: {channel_mention}",
                inline=False
            )
            
        # Create navigation buttons
        class NavButtons(discord.ui.View):
            def __init__(self, cog, current_page, max_pages):
                super().__init__(timeout=60)
                self.cog = cog
                self.current_page = current_page
                self.max_pages = max_pages
                
                # Disable prev button on first page
                if current_page == 1:
                    self.prev_button.disabled = True
                    
                # Disable next button on last page
                if current_page == max_pages:
                    self.next_button.disabled = True
                    
                # Add disable buttons for each subreddit
                for i, (sub_name, _) in enumerate(current_page_items, start=1):
                    self.add_item(DisableButton(cog, sub_name, i))
                
            @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
            async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await self.cog.reddit_autopost_list(interaction, page=self.current_page - 1)
                
            @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await self.cog.reddit_autopost_list(interaction, page=self.current_page + 1)
                
        class DisableButton(discord.ui.Button):
            def __init__(self, cog, subreddit, position):
                super().__init__(
                    label=f"Disable #{position}",
                    style=discord.ButtonStyle.danger,
                    custom_id=f"disable_{subreddit}"
                )
                self.cog = cog
                self.subreddit = subreddit
                
            async def callback(self, interaction: discord.Interaction):
                # Check permissions
                if not interaction.user.guild_permissions.manage_channels:
                    await interaction.response.send_message(
                        "You need 'Manage Channels' permission to disable auto-posting.", 
                        ephemeral=True
                    )
                    return
                    
                # Remove the subreddit
                success = remove_subreddit(interaction.guild.id, self.subreddit)
                
                if success:
                    # Update the store
                    self.cog.autopost_store = get_subreddits(interaction.guild.id)
                    
                    # Send confirmation
                    await interaction.response.send_message(
                        f"✅ Disabled auto-posting for r/{self.subreddit}",
                        ephemeral=True
                    )
                    
                    # Refresh the list
                    await self.cog.reddit_autopost_list(interaction, page=page)
                else:
                    await interaction.response.send_message(
                        f"❌ Failed to disable auto-posting for r/{self.subreddit}",
                        ephemeral=True
                    )
        
        # Send the embed with navigation buttons
        view = NavButtons(self, page, max_pages)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    async def autopost_loop(self):
        """Background task to poll enabled subreddits and post new content"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for guild_id, sub_map in list(self.autopost_store.items()):
                    guild = self.bot.get_guild(int(guild_id))
                    if guild is None:
                        continue
                    for sub_name, cfg in sub_map.items():
                        channel = self.bot.get_channel(cfg['channel_id'])
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
                                    await self.send_reddit_embed(channel, sub_name, newest_post, indicator="NEW")
                                    cfg.setdefault('seen_ids', []).append(newest_post['id'])
                                    cfg['last_posted_id'] = newest_post['id']
                                    cfg['last_post_ts'] = now_ts

                        # BEST flow
                        last_best_ts = cfg.get('last_best_post_ts', 0)
                        if now_ts - last_best_ts >= 300:
                            best_post = fetch_random_best_post(sub_name, limit=100)
                            if best_post and best_post['id'] not in cfg.get('seen_ids', []):
                                await self.send_reddit_embed(channel, sub_name, best_post, indicator="BEST")
                                cfg.setdefault('seen_ids', []).append(best_post['id'])
                                cfg['last_best_post_ts'] = now_ts
                
            except Exception as e:
                logging.error(f"Autopost error: {e}")

            # Wait 30s before checking again
            await asyncio.sleep(30)
            
    async def send_reddit_embed(self, channel, sub_name, post, indicator="NEW"):
        """Send a Reddit post as an embed"""
        try:
            title = post.get('title', 'No Title')
            author = post.get('author', 'Unknown')
            url = post.get('post_url', '')
            image_url = post.get('image_url')
            
            # Skip if no image URL
            if not image_url:
                return None
                
            # Create embed
            if indicator == "NEW":
                color = discord.Color.blue()
                indicator = "🆕 NEW"
            elif indicator == "BEST":
                color = discord.Color.orange()
                indicator = "🏆 BEST"
            else:
                color = discord.Color.greyple()
                
            embed = discord.Embed(
                title=f"{indicator} | {title}",
                url=url,
                color=color
            )
            
            embed.set_image(url=image_url)
            embed.set_author(name=f"Posted by u/{author}")
            
            # Add stats if available
            if 'score' in post:
                embed.add_field(name='👍 Upvotes', value=str(post.get('score', 0)), inline=True)
            if 'num_comments' in post:
                embed.add_field(name='💬 Comments', value=str(post.get('num_comments', 0)), inline=True)
            
            embed.set_footer(text=f"{indicator} • {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC • r/{sub_name}")
            return await channel.send(embed=embed)
        except Exception as e:
            logging.error(f"Error sending reddit embed: {e}")
            return await channel.send(f"**r/{sub_name}** - {title} - <{url}>")

async def setup(bot: commands.Bot):
    """Add the Reddit commands cog to the bot"""
    cog = RedditCommands(bot)
    await bot.add_cog(cog)
    print(f"Registered Reddit commands cog")
