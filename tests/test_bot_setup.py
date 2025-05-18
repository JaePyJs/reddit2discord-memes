"""
Test script for bot setup.

This script tests the bot's setup and extension loading.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

class TestBotSetup(unittest.IsolatedAsyncioTestCase):
    """Test cases for bot setup"""

    async def test_load_extensions(self):
        """Test that the bot loads all extensions"""
        # Create a mock bot
        mock_bot = MagicMock()
        mock_bot.load_extension = AsyncMock()

        # Import the load_extensions function
        from bot.main import load_extensions

        # Call the function with our mock bot
        with patch('bot.main.bot', mock_bot):
            await load_extensions()

        # Check that all extensions were loaded
        expected_extensions = [
            "bot.features.music.commands_setup",
            # "bot.features.memes.commands",  # Temporarily disabled
            "bot.features.reddit.commands",
            "bot.features.ai.commands",
            "bot.features.tenor.commands",
            "bot.features.weather.commands",
            "bot.features.urban.commands",
            # "bot.features.maps.commands",    # Temporarily disabled
            # "bot.features.news.commands",    # Temporarily disabled
            # "bot.features.currency.commands" # Temporarily disabled
        ]

        # Filter out commented extensions
        expected_extensions = [ext for ext in expected_extensions if not ext.startswith('#')]

        # Check that load_extension was called for each extension
        self.assertEqual(mock_bot.load_extension.call_count, len(expected_extensions))

        # Check that each extension was loaded
        for extension in expected_extensions:
            mock_bot.load_extension.assert_any_call(extension)

if __name__ == "__main__":
    unittest.main()
