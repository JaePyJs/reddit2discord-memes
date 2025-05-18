"""
Test script for Tenor GIF commands.

This script tests the functionality of the Tenor GIF commands.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MockInteraction:
    """Mock Discord Interaction for testing commands"""

    def __init__(self):
        self.response = AsyncMock()
        self.followup = AsyncMock()
        self.guild = MagicMock()
        self.guild.name = "Test Guild"
        self.guild_id = 123456
        self.user = MagicMock()
        self.user.id = 123456789
        self.channel = MagicMock()
        self.channel.id = 987654321
        self.channel_id = 987654321

class TestTenorCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Tenor GIF commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Mock the analytics module
        patcher = patch('bot.features.tenor.commands.analytics')
        self.mock_analytics = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Import and patch the Tenor client
        patcher = patch('bot.features.tenor.commands.TenorClient')
        self.mock_tenor_client_class = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Create a mock instance
        self.mock_tenor_client = MagicMock()
        self.mock_tenor_client.initialized = True
        self.mock_tenor_client_class.return_value = self.mock_tenor_client

        # Mock search_gifs method
        self.mock_tenor_client.search_gifs = AsyncMock(return_value=[
            {
                "id": "12345",
                "title": "Test GIF",
                "media_formats": {
                    "gif": {
                        "url": "https://example.com/test.gif",
                        "dims": [480, 270],
                        "size": 1024
                    },
                    "mp4": {
                        "url": "https://example.com/test.mp4",
                        "dims": [480, 270],
                        "size": 512
                    }
                },
                "content_description": "Test GIF Description",
                "url": "https://tenor.com/view/test-12345"
            }
        ])

        # Mock get_trending_gifs method
        self.mock_tenor_client.get_trending_gifs = AsyncMock(return_value=[
            {
                "id": "67890",
                "title": "Trending GIF",
                "media_formats": {
                    "gif": {
                        "url": "https://example.com/trending.gif",
                        "dims": [480, 270],
                        "size": 1024
                    },
                    "mp4": {
                        "url": "https://example.com/trending.mp4",
                        "dims": [480, 270],
                        "size": 512
                    }
                },
                "content_description": "Trending GIF Description",
                "url": "https://tenor.com/view/trending-67890"
            }
        ])

        # Mock extract_gif_url method
        self.mock_tenor_client.extract_gif_url = MagicMock(return_value="https://example.com/test.gif")

        # Import the Tenor commands
        from bot.features.tenor.commands import TenorCommands
        self.tenor_commands = TenorCommands(self.bot)

    async def test_gif_command(self):
        """Test the gif command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.tenor_commands.gif_command.callback

        # Call the callback directly
        await callback(self.tenor_commands, interaction, "test")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Tenor client was called correctly
        self.mock_tenor_client.search_gifs.assert_called_once_with("test", limit=10)

    async def test_gif_command_no_results(self):
        """Test the gif command with no results"""
        interaction = MockInteraction()

        # Mock empty results
        self.mock_tenor_client.search_gifs.return_value = []

        # Get the callback function from the command
        callback = self.tenor_commands.gif_command.callback

        # Call the callback directly
        await callback(self.tenor_commands, interaction, "nonexistent")

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Set up the mock to return the expected content
        interaction.followup.send.return_value = None
        interaction.followup.send.assert_called_once()

        # Manually check if the function was called with the expected content
        called = False
        for call in interaction.followup.send.call_args_list:
            args, kwargs = call
            if 'content' in kwargs and "No GIFs found" in kwargs['content']:
                called = True
                break
            elif len(args) > 0 and isinstance(args[0], str) and "No GIFs found" in args[0]:
                called = True
                break

        self.assertTrue(called, "Expected 'No GIFs found' in the response")

    async def test_trending_gifs_command(self):
        """Test the trending_gifs command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.tenor_commands.trending_gifs_command.callback

        # Call the callback directly
        await callback(self.tenor_commands, interaction)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Tenor client was called correctly
        self.mock_tenor_client.get_trending_gifs.assert_called_once_with(limit=5)

    async def test_trending_gifs_command_no_results(self):
        """Test the trending_gifs command with no results"""
        interaction = MockInteraction()

        # Mock empty results
        self.mock_tenor_client.get_trending_gifs.return_value = []

        # Get the callback function from the command
        callback = self.tenor_commands.trending_gifs_command.callback

        # Call the callback directly
        await callback(self.tenor_commands, interaction)

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Set up the mock to return the expected content
        interaction.followup.send.return_value = None
        interaction.followup.send.assert_called_once()

        # Manually check if the function was called with the expected content
        called = False
        for call in interaction.followup.send.call_args_list:
            args, kwargs = call
            if 'content' in kwargs and "No trending GIFs found" in kwargs['content']:
                called = True
                break
            elif len(args) > 0 and isinstance(args[0], str) and "No trending GIFs found" in args[0]:
                called = True
                break

        self.assertTrue(called, "Expected 'No trending GIFs found' in the response")

if __name__ == "__main__":
    unittest.main()
