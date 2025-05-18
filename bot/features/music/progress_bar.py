"""
Music Player Progress Bar

This module provides functionality to display visual progress indicators for
currently playing tracks in the music player.
"""

import discord
import asyncio
import logging
import time
import math
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta

# Progress bar configuration
PROGRESS_BAR_LENGTH = 20  # Number of characters in the progress bar
PROGRESS_BAR_FILLED = "▰"  # Character for filled portion
PROGRESS_BAR_EMPTY = "▱"  # Character for empty portion
PROGRESS_BAR_UPDATE_INTERVAL = 10  # Update interval in seconds

class ProgressBar:
    """Progress bar for music playback"""
    
    def __init__(self, duration_ms: int, title: str, artist: str = None, 
                album: str = None, album_art: str = None):
        """
        Initialize a progress bar
        
        Args:
            duration_ms: Duration of the track in milliseconds
            title: Track title
            artist: Artist name (optional)
            album: Album name (optional)
            album_art: Album art URL (optional)
        """
        self.duration_ms = duration_ms
        self.title = title
        self.artist = artist
        self.album = album
        self.album_art = album_art
        self.start_time = time.time()
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
        self.message = None
        self.active = True
        self.last_update_time = 0
    
    def pause(self):
        """Pause the progress bar"""
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
    
    def resume(self):
        """Resume the progress bar"""
        if self.paused:
            self.paused = False
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            self.pause_start_time = None
    
    def get_elapsed_ms(self) -> int:
        """
        Get elapsed time in milliseconds
        
        Returns:
            Elapsed time in milliseconds
        """
        if not self.active:
            return 0
            
        if self.paused:
            elapsed = (self.pause_start_time - self.start_time) - self.total_pause_time
        else:
            elapsed = (time.time() - self.start_time) - self.total_pause_time
            
        return int(elapsed * 1000)
    
    def get_progress_percentage(self) -> float:
        """
        Get progress percentage
        
        Returns:
            Progress percentage (0-100)
        """
        elapsed_ms = self.get_elapsed_ms()
        return min(100, (elapsed_ms / self.duration_ms) * 100)
    
    def get_progress_bar(self) -> str:
        """
        Get progress bar string
        
        Returns:
            Progress bar string
        """
        percentage = self.get_progress_percentage()
        filled_length = math.floor(PROGRESS_BAR_LENGTH * (percentage / 100))
        
        bar = PROGRESS_BAR_FILLED * filled_length + PROGRESS_BAR_EMPTY * (PROGRESS_BAR_LENGTH - filled_length)
        
        return bar
    
    def get_time_display(self) -> str:
        """
        Get time display string (elapsed/total)
        
        Returns:
            Time display string
        """
        elapsed_ms = self.get_elapsed_ms()
        elapsed_seconds = elapsed_ms // 1000
        total_seconds = self.duration_ms // 1000
        
        elapsed_str = f"{elapsed_seconds // 60}:{elapsed_seconds % 60:02d}"
        total_str = f"{total_seconds // 60}:{total_seconds % 60:02d}"
        
        return f"{elapsed_str}/{total_str}"
    
    def create_embed(self) -> discord.Embed:
        """
        Create an embed with the progress bar
        
        Returns:
            Discord embed
        """
        progress_bar = self.get_progress_bar()
        time_display = self.get_time_display()
        
        # Create embed
        embed = discord.Embed(
            title="Now Playing",
            description=f"**{self.title}**",
            color=discord.Color.blue()
        )
        
        # Add artist and album if available
        if self.artist:
            embed.add_field(name="Artist", value=self.artist, inline=True)
        if self.album:
            embed.add_field(name="Album", value=self.album, inline=True)
        
        # Add progress bar
        embed.add_field(
            name="Progress",
            value=f"`{progress_bar}` {time_display}",
            inline=False
        )
        
        # Add status
        status = "⏸️ Paused" if self.paused else "▶️ Playing"
        embed.add_field(name="Status", value=status, inline=True)
        
        # Set thumbnail if album art is available
        if self.album_art:
            embed.set_thumbnail(url=self.album_art)
        
        # Set footer
        embed.set_footer(text=f"Use /pause, /resume, or /skip to control playback")
        
        return embed
    
    async def start(self, channel: discord.TextChannel) -> discord.Message:
        """
        Start displaying the progress bar
        
        Args:
            channel: Discord text channel
            
        Returns:
            Discord message
        """
        try:
            # Create initial embed
            embed = self.create_embed()
            
            # Send message
            self.message = await channel.send(embed=embed)
            
            # Start update loop
            asyncio.create_task(self._update_loop())
            
            return self.message
        except Exception as e:
            logging.error(f"Error starting progress bar: {e}")
            self.active = False
            return None
    
    async def _update_loop(self):
        """Update loop for the progress bar"""
        try:
            while self.active and self.message:
                # Check if song has ended
                if self.get_elapsed_ms() >= self.duration_ms and not self.paused:
                    self.active = False
                    break
                
                # Only update every PROGRESS_BAR_UPDATE_INTERVAL seconds
                current_time = time.time()
                if current_time - self.last_update_time >= PROGRESS_BAR_UPDATE_INTERVAL:
                    self.last_update_time = current_time
                    
                    # Update embed
                    embed = self.create_embed()
                    await self.message.edit(embed=embed)
                
                # Sleep to avoid rate limiting
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error in progress bar update loop: {e}")
            self.active = False
    
    def stop(self):
        """Stop the progress bar"""
        self.active = False
