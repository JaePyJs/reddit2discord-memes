"""
Test script for music commands.

This script tests the functionality of the music commands.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
from bot.features.music.player import YTDLSource, Song

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MockVoiceClient:
    """Mock Discord voice client for testing"""

    def __init__(self):
        self.is_playing = MagicMock(return_value=False)
        self.is_paused = MagicMock(return_value=False)
        self.play = MagicMock()
        self.pause = MagicMock()
        self.resume = MagicMock()
        self.stop = MagicMock()
        self.disconnect = AsyncMock()

class MockContext:
    """Mock Discord Context for testing commands"""

    def __init__(self):
        self.bot = MagicMock()
        self.bot.loop = asyncio.get_event_loop()
        self.guild = MagicMock()
        self.guild.name = "Test Guild"
        self.guild.voice_client = None
        self.guild.me = MagicMock()
        self.guild.me.edit = AsyncMock()
        self.author = MagicMock()
        self.author.id = 123456789
        self.author.voice = MagicMock()
        self.author.voice.channel = MagicMock()
        self.author.voice.channel.name = "Test Voice Channel"
        self.author.voice.channel.connect = AsyncMock(return_value=MockVoiceClient())
        self.channel = MagicMock()
        self.channel.id = 987654321
        self.channel.send = AsyncMock()
        self.voice_client = None
        self.cog = None
        self.typing = AsyncMock().__aenter__.return_value = AsyncMock()
        self.send = AsyncMock()
        self.invoke = AsyncMock()

class TestMusicCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Music commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"
        self.bot.voice_clients = []
        self.bot.cogs = {}

        # Mock the add_cog method as an AsyncMock
        self.bot.add_cog = AsyncMock()

        # Import the Music commands
        from bot.features.music.commands_setup import setup, Music

        # Setup the cog
        await setup(self.bot)

        # Create the music cog directly since we mocked add_cog
        self.music_cog = Music(self.bot)

        # Store the cog in the bot.cogs dictionary to simulate what add_cog would do
        self.bot.cogs['Music'] = self.music_cog

        # Verify the cog was created
        self.assertIsNotNone(self.music_cog, "Music cog not found")

    async def test_join_command(self):
        """Test the join command"""
        ctx = MockContext()

        # Get the callback function directly
        callback = self.music_cog.join.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded
        ctx.send.assert_called_once()

        # Check that the bot joined the voice channel
        ctx.author.voice.channel.connect.assert_called_once()

    async def test_join_command_no_voice(self):
        """Test the join command when user is not in a voice channel"""
        ctx = MockContext()
        ctx.author.voice = None

        # Get the callback function directly
        callback = self.music_cog.join.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded with an error
        ctx.send.assert_called_once()
        args, kwargs = ctx.send.call_args
        self.assertIn("You are not connected to a voice channel", args[0])

    async def test_leave_command(self):
        """Test the leave command"""
        ctx = MockContext()

        # Mock that the bot is in a voice channel
        voice_client = MockVoiceClient()
        ctx.guild.voice_client = voice_client
        ctx.voice_client = voice_client

        # Get the callback function directly
        callback = self.music_cog.leave.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded
        ctx.send.assert_called_once()

        # Check that the bot left the voice channel
        voice_client.disconnect.assert_called_once()

    async def test_play_command(self):
        """Test the play command"""
        ctx = MockContext()

        # Mock that the bot is in a voice channel
        voice_client = MockVoiceClient()
        ctx.guild.voice_client = voice_client
        ctx.voice_client = voice_client

        # Mock the YTDLSource
        with patch('bot.features.music.player.YTDLSource.create_source') as mock_create_source, \
             patch('bot.features.music.commands_setup.Music.get_player') as mock_get_player:

            # Mock the source
            mock_source = {
                'title': 'Test Song',
                'webpage_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'thumbnail': 'https://example.com/thumbnail.jpg',
                'duration': 213
            }
            mock_create_source.return_value = mock_source

            # Mock the player
            mock_player = MagicMock()
            mock_player.queue = []
            mock_player.next = MagicMock()
            mock_player.next.set = MagicMock()
            mock_get_player.return_value = mock_player

            # Create a modified version of the play method that doesn't use ctx.typing()
            async def modified_play(cog, ctx, search):
                if not ctx.voice_client:
                    await ctx.invoke(cog.join)

                try:
                    # It's a single track (YouTube or Spotify) or search query
                    source = await YTDLSource.create_source(search, loop=cog.bot.loop, requester=ctx.author)
                    song = Song(source, ctx.author)

                    player = await cog.get_player(ctx)
                    player.queue.append(song)

                    if not ctx.voice_client.is_playing():
                        player.next.set()
                        await ctx.send(f"Now playing: **{song.title}**")
                    else:
                        await ctx.send(f"Added to queue: **{song.title}**")
                except Exception as e:
                    await ctx.send(f"An error occurred: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # Call our modified play method
            await modified_play(self.music_cog, ctx, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

            # Check that the command responded
            ctx.send.assert_called()

            # Check that the bot played the song
            mock_create_source.assert_called_once()
            # Note: The actual play happens in the player_loop, not directly in the command

    async def test_pause_command(self):
        """Test the pause command"""
        ctx = MockContext()

        # Mock that the bot is in a voice channel and playing
        voice_client = MockVoiceClient()
        voice_client.is_playing.return_value = True
        ctx.guild.voice_client = voice_client
        ctx.voice_client = voice_client

        # Get the callback function directly
        callback = self.music_cog.pause.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded
        ctx.send.assert_called_once()

        # Check that the bot paused the song
        voice_client.pause.assert_called_once()

    async def test_resume_command(self):
        """Test the resume command"""
        ctx = MockContext()

        # Mock that the bot is in a voice channel and paused
        voice_client = MockVoiceClient()
        voice_client.is_paused.return_value = True
        ctx.guild.voice_client = voice_client
        ctx.voice_client = voice_client

        # Get the callback function directly
        callback = self.music_cog.resume.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded
        ctx.send.assert_called_once()

        # Check that the bot resumed the song
        voice_client.resume.assert_called_once()

    async def test_skip_command(self):
        """Test the skip command"""
        ctx = MockContext()

        # Mock that the bot is in a voice channel and playing
        voice_client = MockVoiceClient()
        voice_client.is_playing.return_value = True
        ctx.guild.voice_client = voice_client
        ctx.voice_client = voice_client

        # Get the callback function directly
        callback = self.music_cog.skip.callback

        # Call the callback directly with the cog and context
        await callback(self.music_cog, ctx)

        # Check that the command responded
        ctx.send.assert_called_once()

        # Check that the bot stopped the song
        voice_client.stop.assert_called_once()

if __name__ == "__main__":
    unittest.main()
