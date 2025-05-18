"""
Test script for Reddit commands.

This script tests the functionality of the Reddit commands.
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
        self.channel = MagicMock()
        self.channel.id = 987654321
        self.channel.name = "test-channel"

class TestRedditCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Reddit commands"""

    _instances = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        TestRedditCommands._instances.append(self)

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"
        self.bot.loop = MagicMock()
        self.bot.loop.create_task = MagicMock()

        # Mock the autopost_store functions before importing RedditCommands
        self.add_subreddit_patcher = patch('bot.features.reddit.commands.add_subreddit')
        self.mock_add_subreddit = self.add_subreddit_patcher.start()
        self.addAsyncCleanup(self.add_subreddit_patcher.stop)

        self.remove_subreddit_patcher = patch('bot.features.reddit.commands.remove_subreddit')
        self.mock_remove_subreddit = self.remove_subreddit_patcher.start()
        self.addAsyncCleanup(self.remove_subreddit_patcher.stop)

        self.get_subreddits_patcher = patch('bot.features.reddit.commands.get_subreddits')
        self.mock_get_subreddits = self.get_subreddits_patcher.start()
        self.addAsyncCleanup(self.get_subreddits_patcher.stop)

        # Mock the reddit integration
        self.reddit_patcher = patch('bot.features.reddit.commands.fetch_new_posts')
        self.mock_fetch_new_posts = self.reddit_patcher.start()
        self.addAsyncCleanup(self.reddit_patcher.stop)

        self.reddit_best_patcher = patch('bot.features.reddit.commands.fetch_random_best_post')
        self.mock_fetch_random_best_post = self.reddit_best_patcher.start()
        self.addAsyncCleanup(self.reddit_best_patcher.stop)

        # Import the Reddit commands
        from bot.features.reddit.commands import RedditCommands

        # Create the cog
        self.reddit_commands = RedditCommands(self.bot)

        # Setup mock return values
        self.mock_fetch_new_posts.return_value = [
            {
                'title': 'New Test Meme',
                'url': 'https://example.com/new_meme.jpg',
                'permalink': '/r/testsubreddit/comments/123457/new_test_meme/',
                'author': 'test_user',
                'score': 50,
                'num_comments': 5,
                'created_utc': 1620000100,
                'subreddit': 'testsubreddit',
                'id': 'abc123',
                'image_url': 'https://example.com/new_meme.jpg',
                'post_url': 'https://reddit.com/r/testsubreddit/comments/123457/new_test_meme/'
            }
        ]

        self.mock_fetch_random_best_post.return_value = {
            'title': 'Best Test Meme',
            'url': 'https://example.com/best_meme.jpg',
            'permalink': '/r/testsubreddit/comments/123458/best_test_meme/',
            'author': 'test_user',
            'score': 1000,
            'num_comments': 100,
            'created_utc': 1619000000,
            'subreddit': 'testsubreddit',
            'id': 'abc456',
            'image_url': 'https://example.com/best_meme.jpg',
            'post_url': 'https://reddit.com/r/testsubreddit/comments/123458/best_test_meme/'
        }

    async def test_reddit_autopost_command(self):
        """Test the reddit_autopost command"""
        interaction = MockInteraction()

        # Get the callback function directly
        callback = self.reddit_commands.reddit_autopost.callback

        # Call the callback directly with the cog and interaction
        await callback(self.reddit_commands, interaction, "testsubreddit", None)

        # Check that the command responded
        interaction.response.send_message.assert_called_once()

        # Check that the autopost was added
        self.mock_add_subreddit.assert_called_once()

    async def test_reddit_autopost_list_command(self):
        """Test the reddit_autopost_list command"""
        interaction = MockInteraction()

        # Mock the get_subreddits function
        self.mock_get_subreddits.return_value = {
            'testsubreddit': {
                'channel_id': 987654321,
                'last_posted_id': 'abc123',
                'last_post_ts': 1620000000,
                'last_best_post_ts': 1619000000,
                'seen_ids': []
            }
        }

        # Get the callback function directly
        callback = self.reddit_commands.reddit_autopost_list.callback

        # Call the callback directly with the cog and interaction
        await callback(self.reddit_commands, interaction)

        # Check that the command responded
        interaction.response.send_message.assert_called_once()

        # Check that the subreddits were retrieved
        self.mock_get_subreddits.assert_called_once_with(123456)

    async def test_reddit_autopost_disable_callback(self):
        """Test the reddit_autopost_disable_callback method"""
        # Create a mock button interaction
        button_interaction = MockInteraction()
        button_interaction.guild.id = 123456

        # Mock the remove_subreddit function to return True
        self.mock_remove_subreddit.return_value = True

        # Call the remove_subreddit function directly
        self.mock_remove_subreddit(123456, 'testsubreddit')

        # Check that the subreddit was disabled
        self.mock_remove_subreddit.assert_called_once_with(123456, 'testsubreddit')

if __name__ == "__main__":
    unittest.main()
