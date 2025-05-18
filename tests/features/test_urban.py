"""
Test script for Urban Dictionary commands.

This script tests the functionality of the Urban Dictionary commands.
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

class TestUrbanCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Urban Dictionary commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Mock the analytics module
        patcher = patch('bot.features.urban.commands.analytics')
        self.mock_analytics = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Import and patch the Urban Dictionary client
        patcher = patch('bot.features.urban.commands.UrbanDictionaryClient')
        self.mock_urban_client_class = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Create a mock instance
        self.mock_urban_client = MagicMock()
        self.mock_urban_client.initialized = True
        self.mock_urban_client_class.return_value = self.mock_urban_client

        # Mock define method
        self.mock_urban_client.define = AsyncMock(return_value=[
            {
                "definition": "Test definition",
                "permalink": "https://www.urbandictionary.com/define.php?term=test",
                "thumbs_up": 1000,
                "thumbs_down": 100,
                "author": "test_user",
                "word": "test",
                "example": "This is a test example."
            }
        ])

        # Mock random method
        self.mock_urban_client.random = AsyncMock(return_value=[
            {
                "definition": "Random definition",
                "permalink": "https://www.urbandictionary.com/define.php?term=random",
                "thumbs_up": 500,
                "thumbs_down": 50,
                "author": "random_user",
                "word": "random",
                "example": "This is a random example."
            }
        ])

        # Mock format_definition method
        self.mock_urban_client.format_definition = MagicMock(return_value="**test**\n\nTest definition\n\n*Example:*\nThis is a test example.\n\n👍 1000 | 👎 100 | by test_user")

        # Import the Urban Dictionary commands
        from bot.features.urban.commands import UrbanDictionaryCommands
        self.urban_commands = UrbanDictionaryCommands(self.bot)

    async def test_define_command(self):
        """Test the define command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.urban_commands.define_command.callback

        # Call the callback directly
        await callback(self.urban_commands, interaction, "test")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Urban Dictionary client was called correctly
        self.mock_urban_client.define.assert_called_once_with("test")

    async def test_define_command_no_results(self):
        """Test the define command with no results"""
        interaction = MockInteraction()

        # Mock empty results
        self.mock_urban_client.define.return_value = []

        # Get the callback function from the command
        callback = self.urban_commands.define_command.callback

        # Call the callback directly
        await callback(self.urban_commands, interaction, "nonexistent")

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

    async def test_urban_random_command(self):
        """Test the urban_random command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.urban_commands.random_command.callback

        # Call the callback directly
        await callback(self.urban_commands, interaction)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Urban Dictionary client was called correctly
        self.mock_urban_client.random.assert_called_once()

    async def test_urban_random_command_no_results(self):
        """Test the urban_random command with no results"""
        interaction = MockInteraction()

        # Mock empty results
        self.mock_urban_client.random.return_value = []

        # Get the callback function from the command
        callback = self.urban_commands.random_command.callback

        # Call the callback directly
        await callback(self.urban_commands, interaction)

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

if __name__ == "__main__":
    unittest.main()
