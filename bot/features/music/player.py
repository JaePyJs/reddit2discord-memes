import asyncio
import discord
import functools
import logging
import yt_dlp
import re
import time
import datetime
from collections import deque
from discord.ext import commands, tasks
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, parse_qs

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
    """Enhanced class representing a song in the queue"""
    def __init__(self, source: dict, requester: discord.Member):
        self.source = source
        self.requester = requester
        self.start_time = None
        self.message_id = None  # ID of the now playing message for updating progress

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
    def album_art(self) -> str:
        # Try to get album art from Spotify data, fall back to thumbnail
        return self.source.get('album_art', self.thumbnail)

    @property
    def duration(self) -> int:
        """Get duration in seconds"""
        return self.source.get('duration', 0)
        
    @property
    def duration_string(self) -> str:
        """Get formatted duration string"""
        duration = self.duration
        if duration:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return "Unknown duration"
        
    @property
    def artist(self) -> str:
        """Get artist name"""
        return self.source.get('artist', 'Unknown artist')
        
    @property
    def album(self) -> str:
        """Get album name"""
        return self.source.get('album', 'Unknown album')

    def create_embed(self, show_progress=False) -> discord.Embed:
        """Create an embed for the song with optional progress bar"""
        embed = discord.Embed(
            title="Now Playing",
            description=f"[{self.title}]({self.url})",
            color=discord.Color.blurple()
        )
        
        # Use album art if available, otherwise use thumbnail
        if self.album_art:
            embed.set_thumbnail(url=self.album_art)
        elif self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
            
        # Add artist and album if available
        if self.artist != 'Unknown artist':
            embed.add_field(name="Artist", value=self.artist, inline=True)
        if self.album != 'Unknown album':
            embed.add_field(name="Album", value=self.album, inline=True)
            
        # Add duration
        embed.add_field(name="Duration", value=self.duration_string, inline=True)
        
        # Add progress bar if requested and song is playing
        if show_progress and self.start_time and self.duration:
            elapsed = time.time() - self.start_time
            progress = min(elapsed / self.duration, 1.0)  # Cap at 100%
            
            # Create progress bar (20 characters wide)
            bar_length = 20
            filled_length = int(bar_length * progress)
            bar = "▓" * filled_length + "░" * (bar_length - filled_length)
            
            # Format elapsed/total time
            elapsed_str = str(datetime.timedelta(seconds=int(elapsed)))
            if elapsed_str.startswith('0:'):
                elapsed_str = elapsed_str[2:]  # Remove leading 0:
            total_str = self.duration_string
            
            embed.add_field(
                name="Progress", 
                value=f"`{elapsed_str} {bar} {total_str}`", 
                inline=False
            )
        
        embed.add_field(name="Requested by", value=self.requester.mention, inline=True)
        
        # Add source info
        if 'spotify' in self.source:
            embed.set_footer(text=f"Spotify Track • Playing via YouTube")
        else:
            embed.set_footer(text=f"Source: YouTube")
            
        return embed

class MusicPlayer:
    """Enhanced music player for a guild"""
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
        self.now_playing_message = None
        
        # Start the player loop and progress updater
        ctx.bot.loop.create_task(self.player_loop())
        self.progress_updater.start()

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
                    self.progress_updater.cancel()
                    return self.destroy(self.guild)
                continue

            # Get the source URL
            source_url = self.current.source.get('url')
            if not source_url:
                await self.channel.send("Error: Could not get audio source. Skipping...")
                self.current = None
                continue

            # Set the start time for progress tracking
            self.current.start_time = time.time()

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
                continue

            # Send the now playing embed with progress bar
            embed = self.current.create_embed(show_progress=True)
            self.now_playing_message = await self.channel.send(embed=embed)
            self.current.message_id = self.now_playing_message.id

            # Wait for the song to finish
            await self.next.wait()

            # Clear the current song if not looping
            if not self.loop:
                self.current = None
                self.now_playing_message = None

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
        self.progress_updater.cancel()
        return self.bot.loop.create_task(self.cog.cleanup(guild))

    async def add_songs_to_queue(self, songs: list):
        """Add multiple songs to the queue at once"""
        self.queue.extend(songs)
        # If not playing and there are songs, trigger the player
        if not self.guild.voice_client.is_playing() and songs:
            self.next.set()
            
    @tasks.loop(seconds=15.0)
    async def progress_updater(self):
        """Update the progress bar in the now playing message"""
        if not self.current or not self.now_playing_message or not self.current.start_time:
            return
            
        try:
            # Update the embed with current progress
            updated_embed = self.current.create_embed(show_progress=True)
            await self.now_playing_message.edit(embed=updated_embed)
        except Exception as e:
            logging.error(f"Error updating progress bar: {e}")
            
    @progress_updater.before_loop
    async def before_progress_updater(self):
        """Wait for the bot to be ready before starting the progress updater"""
        await self.bot.wait_until_ready()

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
                    from bot.features.music.spotify import SpotifyClient
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
            
        # Add Spotify metadata if available
        if re.match(spotify_pattern, search) and cls.spotify_client:
            try:
                spotify_data = await cls.spotify_client.parse_spotify_url(search)
                if isinstance(spotify_data, dict):
                    processed_data['artist'] = spotify_data.get('artist')
                    processed_data['album'] = spotify_data.get('album')
                    processed_data['album_art'] = spotify_data.get('album_art')
                    processed_data['spotify'] = True
                elif isinstance(spotify_data, list) and spotify_data:
                    processed_data['artist'] = spotify_data[0].get('artist')
                    processed_data['album'] = spotify_data[0].get('album')
                    processed_data['album_art'] = spotify_data[0].get('album_art')
                    processed_data['spotify'] = True
            except Exception as e:
                logging.error(f"Error adding Spotify metadata: {e}")

        return processed_data
