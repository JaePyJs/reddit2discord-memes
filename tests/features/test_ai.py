"""
Test script for AI chat commands.

This script tests the functionality of the AI chat commands.
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
        self.guild.id = 123456
        self.guild.name = "Test Guild"
        self.user = MagicMock()
        self.user.id = 123456789
        self.user.name = "Test User"
        self.channel = MagicMock()
        self.channel.id = 987654321
        self.channel.name = "test-channel"

class TestAICommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for AI chat commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Import the AI commands
        from bot.features.ai.commands import AICommands

        # Mock the AI chat functions
        patcher = patch('bot.features.ai.commands.set_ai_channel')
        self.mock_set_ai_channel = patcher.start()
        self.mock_set_ai_channel.return_value = (True, None)
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.is_ai_channel')
        self.mock_is_ai_channel = patcher.start()
        self.mock_is_ai_channel.return_value = True
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.get_ai_channel')
        self.mock_get_ai_channel = patcher.start()
        self.mock_get_ai_channel.return_value = 987654321
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.get_ai_response')
        self.mock_get_ai_response = patcher.start()
        self.mock_get_ai_response.return_value = "This is a test AI response."
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.clear_chat_history')
        self.mock_clear_chat_history = patcher.start()
        self.mock_clear_chat_history.return_value = True
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.set_user_preference')
        self.mock_set_user_preference = patcher.start()
        self.mock_set_user_preference.return_value = True
        self.addAsyncCleanup(patcher.stop)

        patcher = patch('bot.features.ai.commands.get_user_preferences')
        self.mock_get_user_preferences = patcher.start()
        self.mock_get_user_preferences.return_value = {
            "tone": "neutral",
            "emoji_level": "moderate",
            "use_name": True
        }
        self.addAsyncCleanup(patcher.stop)
        # Create the cog
        self.ai_commands = AICommands(self.bot)

    async def test_ai_chat_set_command(self):
        """Test the ai_chat_set command"""
        interaction = MockInteraction()

        # Mock permissions
        interaction.channel.permissions_for = MagicMock(return_value=MagicMock(manage_channels=True))

        # Get the callback function from the command
        callback = self.ai_commands.ai_chat_set.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction)

        # Check that the command responded
        interaction.response.send_message.assert_called_once()

        # Check that the chat channel was set
        self.mock_set_ai_channel.assert_called_once_with(123456, 987654321)

    async def test_clear_chat_command(self):
        """Test the clear_chat command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.ai_commands.clear_chat.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction)

        # Check that the command responded
        interaction.response.send_message.assert_called_once()

        # Check that the chat history was cleared
        self.mock_clear_chat_history.assert_called_once_with(987654321, None)

    async def test_ai_chat_help_command(self):
        """Test the ai_chat_help command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.ai_commands.ai_chat_help.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction)

        # Check that the command responded
        interaction.response.send_message.assert_called_once()

    async def test_delete_messages_command(self):
        """Test the delete_messages command"""
        interaction = MockInteraction()

        # Mock permissions and channel.purge method
        interaction.channel.permissions_for = MagicMock(return_value=MagicMock(manage_messages=True))
        interaction.channel.purge = AsyncMock()

        # Get the callback function from the command
        callback = self.ai_commands.delete_messages.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction, 10)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the messages were deleted
        interaction.channel.purge.assert_called_once()

    async def test_dm_chat_command(self):
        """Test the dm_chat command"""
        interaction = MockInteraction()

        # Mock the user.create_dm method
        dm_channel = MagicMock()
        dm_channel.send = AsyncMock()
        interaction.user.create_dm = AsyncMock(return_value=dm_channel)

        # Get the callback function from the command
        callback = self.ai_commands.dm_chat.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that a DM was sent
        dm_channel.send.assert_called_once()

    async def test_ai_preferences_command(self):
        """Test the ai_preferences command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.ai_commands.ai_preferences.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction, "casual", "moderate", True)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the preferences were set
        self.mock_set_user_preference.assert_called()

    async def test_ai_preferences_view_command(self):
        """Test the ai_preferences_view command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.ai_commands.ai_preferences_view.callback

        # Call the callback directly
        await callback(self.ai_commands, interaction)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the preferences were retrieved
        self.mock_get_user_preferences.assert_called_once_with('123456789')

if __name__ == "__main__":
    unittest.main()
