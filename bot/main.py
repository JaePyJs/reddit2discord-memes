import discord
from discord import app_commands, Intents
from discord.ext import commands
import os
import logging
import asyncio
from bot.utils.config import DISCORD_TOKEN
from bot.integrations.reddit import fetch_new_posts, fetch_random_best_post
from bot.utils.template_manager import TemplateManager
from bot.utils import db
from PIL import Image, ImageDraw, ImageFont
import io
import re
from bot.utils.text_utils import draw_wrapped_text
from bot.utils.font_utils import get_best_fit_font
from bot.utils.color_utils import get_average_luminance, pick_text_color
from bot.utils.autopost_store import load_store, save_store, add_subreddit, remove_subreddit, get_subreddits
from typing import Optional, Dict, Any, List

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

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

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
                                    break
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
            save_store(autopost_store)
        except Exception as e:
            print(f"Autopost loop error: {e}")
        await asyncio.sleep(60)  # poll every 60 seconds to align with 5-min posting limit

def send_reddit_embed(channel, sub_name, post, indicator="NEW"):
    p_type = post.get('type', 'image')
    color = 0x3498db if indicator == "NEW" else 0xf39c12
    embed = discord.Embed(title=f"[{indicator}] {post['title']}", color=color, timestamp=discord.utils.utcnow())
    embed.url = post['post_url']
    embed.set_author(name=f"r/{sub_name}")

    if p_type == 'image':
        embed.set_image(url=post['media_url'])
    elif p_type == 'video':
        embed.description = f"[Click to view video]({post['media_url']})"
        embed.set_footer(text="Video content – cannot embed directly")
    elif p_type == 'text':
        embed.description = post.get('content_text', '')[:2048]

    embed.add_field(name='👍 Upvotes', value=str(post.get('ups', 0)), inline=True)
    embed.add_field(name='💬 Comments', value=str(post.get('num_comments', 0)), inline=True)

    embed.set_footer(text=f"{indicator} • {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC • r/{sub_name}")
    return channel.send(embed=embed)

# Slash command to enable auto-post for a subreddit in current channel
@bot.tree.command(guild=discord.Object(id=781372590278311957), name='reddit_autopost', description='Enable Reddit auto-posting for a subreddit URL (e.g., https://www.reddit.com/r/memes/)')
@app_commands.describe(
    url='Reddit subreddit URL to enable auto-posting',
    channel='Target channel to post in (defaults to current channel)'
)
async def reddit_autopost(interaction: discord.Interaction, url: str, channel: Optional[discord.TextChannel] = None):
    pattern = r'https?://(www\.)?reddit\.com/r/([A-Za-z0-9_]+)/?'
    m = re.match(pattern, url)
    if not m:
        await interaction.response.send_message('Invalid URL. Provide something like https://www.reddit.com/r/memes/', ephemeral=True)
        return
    subreddit = m.group(2)

    target_channel = channel or interaction.channel  # default to invoking channel
    # ensure bot has permission to post there
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message('I do not have permission to send messages in that channel.', ephemeral=True)
        return

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
                # remove from list and recalc pages
                self.sub_items = [item for item in self.sub_items if item[0] != subreddit]
                self.total_pages = max(1, (len(self.sub_items) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
                if self.page >= self.total_pages:
                    self.page = self.total_pages - 1
                global autopost_store
                autopost_store = load_store()
                self.refresh_items()
                await interaction.response.edit_message(embed=self.make_embed(), view=self)
            else:
                await interaction.response.send_message('Failed to disable (not found).', ephemeral=True)

        return discord.ui.Button(label=f"Disable r/{subreddit}", style=discord.ButtonStyle.danger, callback=disable_callback)

    def _make_nav_button(self, label: str, direction: str, disabled: bool) -> discord.ui.Button:
        async def nav_callback(interaction: discord.Interaction):
            if direction == "prev" and self.page > 0:
                self.page -= 1
            elif direction == "next" and self.page < self.total_pages - 1:
                self.page += 1
            self.refresh_items()
            await interaction.response.edit_message(embed=self.make_embed(), view=self)

        return discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=disabled, callback=nav_callback)

# Slash command to list enabled subreddits with disable buttons
@bot.tree.command(guild=discord.Object(id=781372590278311957), name='reddit_autopost_list', description='Manage active Reddit auto-post subreddits')
async def reddit_autopost_list(interaction: discord.Interaction):
    subs = get_subreddits(interaction.guild.id)
    if not subs:
        await interaction.response.send_message('No auto-post subreddits configured for this server.', ephemeral=True)
        return
    view = AutoPostListView(interaction.guild.id, subs)
    await interaction.response.send_message(embed=view.make_embed(), view=view, ephemeral=True)

# Meme creation command
@bot.tree.command(guild=discord.Object(id=781372590278311957), name='meme_create', description='Create a meme from a template! Optionally tag up to 5 friends.')
@app_commands.describe(
    template='Template image filename',
    top_text='Top text',
    bottom_text='Bottom text',
    top_x='Top text X position (default 10)',
    top_y='Top text Y position (default 10)',
    bottom_x='Bottom text X position (default 10)',
    bottom_y='Bottom text Y position (default image height - 50)',
    font_name='Font name (default Arial)',
    font_size='Font size (default 36)',
    font_color='Font color (default white, e.g. "white" or "#FFFFFF")',
    outline_color='Outline color (default black)',
    tags='(Optional) Tag friends (comma-separated @mentions or IDs, up to 5)'
)
async def meme_create(
    interaction: discord.Interaction,
    template: str,
    top_text: str = '',
    bottom_text: str = '',
    top_x: int = 10,
    top_y: int = 10,
    bottom_x: int = 10,
    bottom_y: int = 250,
    font_name: str = 'Arial',
    font_size: int = 36,
    font_color: str = 'white',
    outline_color: str = 'black',
    tags: str = ''
):
    log_command_execution('meme_create', interaction)
    tm = TemplateManager()
    templates = tm.list_templates()
    if template not in templates:
        await interaction.response.send_message(f'Template not found. Available: {", ".join(templates)}', ephemeral=True)
        return

    template_path = f'templates/{template}'
    try:
        img = Image.open(template_path).convert('RGB')
        draw = ImageDraw.Draw(img)

        font_path_guess = f'{font_name}.ttf' if not font_name.lower().endswith('.ttf') else font_name
        font_path = font_path_guess if os.path.exists(font_path_guess) else None

        w, h = img.size

        # Sanitize text (remove custom Discord emojis)
        sanitize = lambda t: re.sub(r'<:.*?:\d+>', '', t)
        top_text = sanitize(top_text)
        bottom_text = sanitize(bottom_text)

        # Calculate bounding boxes
        top_box = (top_x, top_y, w - top_x * 2, int(h / 3))
        by = bottom_y if bottom_y is not None else h - 50
        bottom_box = (bottom_x, by, w - bottom_x * 2, int(h / 3))

        # Determine best fit fonts
        top_font = get_best_fit_font(top_text, font_path, top_box[2], top_box[3], start_size=font_size)
        bottom_font = get_best_fit_font(bottom_text, font_path, bottom_box[2], bottom_box[3], start_size=font_size)

        # Adaptive text colors
        top_text_color = pick_text_color(get_average_luminance(img, top_box))
        bottom_text_color = pick_text_color(get_average_luminance(img, bottom_box))

        # Helper to draw outlined/wrapped text
        def draw_with_outline(box, text, font, fill_color):
            x, y, w_box, h_box = box
            for dx in [-2, 0, 2]:
                for dy in [-2, 0, 2]:
                    if dx == 0 and dy == 0:
                        continue
                    draw_wrapped_text(draw, text, font, (x + dx, y + dy, w_box, h_box), outline_color)
            draw_wrapped_text(draw, text, font, box, fill_color)

        draw_with_outline(top_box, top_text, top_font, top_text_color)
        draw_with_outline(bottom_box, bottom_text, bottom_font, bottom_text_color)

        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        # Prepare mentions if any
        tag_mentions = ''
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()][:5]
            tag_mentions = ' '.join([t if t.startswith('<@') else f'<@{t}>' for t in tag_list])

        await interaction.response.send_message(
            file=discord.File(buf, filename='meme.png'),
            content=tag_mentions if tag_mentions else None
        )

        # Log to DB
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO meme_history (user_id, command, meme_url) VALUES (?, ?, ?)',
            (str(interaction.user.id), '/meme_create', template)
        )
        conn.commit()
        conn.close()

    except Exception as e:
        logging.error(f'Meme creation error: {e}')
        await interaction.response.send_message('Failed to create meme. Please try again.', ephemeral=True)

log_command_registration('meme_create')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    
    # Sync guild commands first (appear instantly)
    guild = discord.Object(id=781372590278311957)
    guild_commands = await bot.tree.sync(guild=guild)
    print(f'Synced {len(guild_commands)} guild commands')
    
    # Then sync global commands (take time to appear)
    global_commands = await bot.tree.sync()
    print(f'Synced {len(global_commands)} global commands')
    
    print('Bot is ready!')
    
    # Start the background auto-post loop
    bot.loop.create_task(autopost_loop())

# Run the bot
bot.run(DISCORD_TOKEN)
