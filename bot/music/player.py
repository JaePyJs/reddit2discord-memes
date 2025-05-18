import asyncio
import discord
import functools
import logging
import yt_dlp
import re
from collections import deque
from discord.ext import commands
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, parse_qs
from bot.music.spotify import SpotifyClient

# Configure YT-DLP
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # Bind to ipv4
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class Song:
    """Class representing a song in the queue"""
    def __init__(self, source: dict, requester: discord.Member):
        self.source = source
        self.requester = requester

    @property
    def title(self) -> str:
        return self.source.get('title', 'Unknown title')

    @property
    def url(self) -> str:
        return self.source.get('webpage_url', 'https://www.youtube.com')

    @property
    def thumbnail(self) -> str:
        return self.source.get('thumbnail', '')

    @property
    def duration(self) -> str:
        duration = self.source.get('duration')
        if duration:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return "Unknown duration"

    def create_embed(self) -> discord.Embed:
        """Create an embed for the song"""
        embed = discord.Embed(
            title="Now Playing",
            description=f"[{self.title}]({self.url})",
            color=discord.Color.blurple()
        )
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        embed.add_field(name="Duration", value=self.duration)
        embed.add_field(name="Requested by", value=self.requester.mention)
        embed.set_footer(text=f"Source: YouTube")
        return embed

class MusicPlayer:
    """Music player for a guild"""
    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog

        self.queue = deque()
        self.next = asyncio.Event()
        self.current: Optional[Song] = None
        self.volume = 0.5
        self.loop = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Main player loop"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            # Try to get a song from the queue
            try:
                if not self.loop:
                    # Get a new song if not looping
                    self.current = self.queue.popleft() if self.queue else None
                # If looping, self.current stays the same
            except IndexError:
                # No more songs in the queue
                await asyncio.sleep(1)
                continue

            if not self.current:
                # No song to play, wait for more songs
                try:
                    async with asyncio.timeout(300):  # Wait 5 minutes
                        await self.next.wait()
                except asyncio.TimeoutError:
                    # Timed out waiting for songs, cleanup
                    return self.destroy(self.guild)
                continue

            # Get the source URL
            source_url = self.current.source.get('url')
            if not source_url:
                await self.channel.send("Error: Could not get audio source. Skipping...")
                self.current = None
                continue

            # Create FFmpeg audio source
            try:
                source = discord.FFmpegPCMAudio(source_url, **ffmpeg_options)
                source = discord.PCMVolumeTransformer(source, volume=self.volume)

                # Play the song
                self.guild.voice_client.play(
                    source,
                    after=lambda error: self.bot.loop.call_soon_threadsafe(
                        lambda: self._handle_playback_error(error)
                    )
                )
            except Exception as e:
                logging.error(f"Error playing audio: {e}")
                asyncio.run_coroutine_threadsafe(
                    self.channel.send(f"Error playing audio: {str(e)}. Skipping..."),
                    self.bot.loop
                )
                self.bot.loop.call_soon_threadsafe(self.next.set)

            # Send the now playing embed
            await self.channel.send(embed=self.current.create_embed())

            # Wait for the song to finish
            await self.next.wait()

            # Clear the current song if not looping
            if not self.loop:
                self.current = None

    def _handle_playback_error(self, error):
        """Handle errors that occur during playback"""
        if error:
            logging.error(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(
                self.channel.send(f"An error occurred during playback: {str(error)}"),
                self.bot.loop
            )
        # Set the next event regardless of error to continue the queue
        self.next.set()

    def destroy(self, guild):
        """Destroy the player and disconnect"""
        return self.bot.loop.create_task(self.cog.cleanup(guild))

    async def add_songs_to_queue(self, songs: list):
        """Add multiple songs to the queue at once"""
        self.queue.extend(songs)
        # If not playing and there are songs, trigger the player
        if not self.guild.voice_client.is_playing() and songs:
            self.next.set()

class YTDLSource:
    """Source for YouTube audio"""
    spotify_client = None
    
    @classmethod
    async def create_source(cls, search: str, *, loop=None, requester=None):
        """Create a source from a search query or URL"""
        loop = loop or asyncio.get_event_loop()
        
        # Handle Spotify URLs
        spotify_pattern = r'https?://open\.spotify\.com/(track|album|playlist)/[a-zA-Z0-9]+'
        if re.match(spotify_pattern, search):
            try:
                # Process Spotify URL
                if cls.spotify_client is None:
                    from bot.music.spotify import SpotifyClient
                    cls.spotify_client = SpotifyClient()
                
                # Make sure the Spotify client is initialized
                if not cls.spotify_client.initialized:
                    logging.error("Spotify client not initialized. Check credentials.")
                    raise Exception("Spotify client not initialized. Please check your API credentials.")
                
                # Try to parse the Spotify URL
                spotify_data = await cls.spotify_client.parse_spotify_url(search)
                
                if isinstance(spotify_data, list):
                    # Multiple tracks (playlist or album)
                    if not spotify_data:
                        raise Exception("No tracks found in Spotify playlist/album")
                    
                    # Just process the first track for now and return info
                    track = spotify_data[0]
                    search = track['search_query']
                    logging.info(f"Spotify playlist/album detected. First track: {track['title']} by {track['artist']}")
                    # We could add all tracks to queue here if needed
                else:
                    # Single track
                    search = spotify_data['search_query']
                    logging.info(f"Spotify track detected: {spotify_data['title']} by {spotify_data['artist']}")
            except Exception as e:
                logging.error(f"Error processing Spotify URL: {e}")
                raise Exception(f"Error processing Spotify URL: {str(e)}")

        # Process the search query
        partial = functools.partial(ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise Exception(f"Could not find anything that matches `{search}`")

        if 'entries' in data:
            # Take the first item from a playlist
            data = data['entries'][0]

        # Get the full data
        partial = functools.partial(ytdl.extract_info, data['webpage_url'], download=False)
        processed_data = await loop.run_in_executor(None, partial)

        if processed_data is None:
            raise Exception(f"Could not fetch `{search}`")

        return processed_data
