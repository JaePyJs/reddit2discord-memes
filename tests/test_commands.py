"""
Test script for Discord commands.

This script tests the functionality of the Discord commands by simulating interactions.
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

class MockInteraction:
    """Mock Discord Interaction for testing commands"""

    def __init__(self):
        self.response = AsyncMock()
        self.followup = AsyncMock()
        self.guild = MagicMock()
        self.guild.name = "Test Guild"
        self.user = MagicMock()
        self.user.id = 123456789
        self.channel = MagicMock()
        self.channel.id = 987654321

class TestMapsCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Maps commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Import and patch the Maps client
        with patch('bot.features.maps.api.MapsClient') as mock_client_class:
            # Set up the mock client
            self.mock_maps_client = mock_client_class.return_value
            self.mock_maps_client.initialized = True

            # Mock geocode method
            self.mock_maps_client.geocode.return_value = {
                "status": "OK",
                "results": [{
                    "formatted_address": "New York, NY, USA",
                    "geometry": {
                        "location": {
                            "lat": 40.7128,
                            "lng": -74.0060
                        }
                    }
                }]
            }

            # Mock directions method
            self.mock_maps_client.get_directions.return_value = {
                "status": "OK",
                "routes": [{
                    "legs": [{
                        "start_address": "New York, NY, USA",
                        "end_address": "Boston, MA, USA",
                        "distance": {"text": "215 mi"},
                        "duration": {"text": "3 hours 45 mins"},
                        "steps": [
                            {"html_instructions": "Head north", "distance": {"text": "0.2 mi"}},
                            {"html_instructions": "Turn right", "distance": {"text": "0.5 mi"}},
                            {"html_instructions": "Continue on I-95", "distance": {"text": "200 mi"}},
                        ]
                    }],
                    "overview_polyline": {"points": "abc123"}
                }]
            }

            # Mock places nearby method
            self.mock_maps_client.get_places_nearby.return_value = {
                "status": "OK",
                "results": [
                    {
                        "name": "Test Restaurant",
                        "vicinity": "123 Test St",
                        "rating": 4.5,
                        "opening_hours": {"open_now": True},
                        "geometry": {"location": {"lat": 40.7128, "lng": -74.0060}}
                    },
                    {
                        "name": "Another Place",
                        "vicinity": "456 Test Ave",
                        "rating": 4.0,
                        "opening_hours": {"open_now": False},
                        "geometry": {"location": {"lat": 40.7129, "lng": -74.0061}}
                    }
                ]
            }

            # Import the Maps commands
            from bot.features.maps.commands import MapsCommands
            self.maps_commands = MapsCommands(self.bot)

    async def test_location_command(self):
        """Test the location command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.maps_commands.location_command.callback

        # Call the callback directly
        await callback(self.maps_commands, interaction, "New York")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Maps client was called correctly
        self.mock_maps_client.geocode.assert_called_once_with("New York")

    async def test_directions_command(self):
        """Test the directions command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.maps_commands.directions_command.callback

        # Call the callback directly
        await callback(self.maps_commands, interaction, "New York", "Boston", "driving")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Maps client was called correctly
        self.mock_maps_client.get_directions.assert_called_once_with("New York", "Boston", "driving")

    async def test_nearby_command(self):
        """Test the nearby command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.maps_commands.nearby_command.callback

        # Call the callback directly
        await callback(self.maps_commands, interaction, "New York", "restaurant", 1000)

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Maps client was called correctly
        self.mock_maps_client.get_places_nearby.assert_called_once_with("New York", 1000, "restaurant")

class TestNewsCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for News commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Import and patch the News client
        with patch('bot.features.news.api.NewsClient') as mock_client_class:
            # Set up the mock client
            self.mock_news_client = mock_client_class.return_value
            self.mock_news_client.initialized = True

            # Mock top headlines method
            self.mock_news_client.get_top_headlines.return_value = {
                "status": "ok",
                "totalResults": 2,
                "articles": [
                    {
                        "source": {"id": "test", "name": "Test News"},
                        "title": "Test Headline",
                        "description": "This is a test headline",
                        "url": "https://example.com/news/1",
                        "urlToImage": "https://example.com/image1.jpg",
                        "publishedAt": "2023-05-22T12:00:00Z"
                    },
                    {
                        "source": {"id": "test2", "name": "Test News 2"},
                        "title": "Another Headline",
                        "description": "This is another test headline",
                        "url": "https://example.com/news/2",
                        "urlToImage": "https://example.com/image2.jpg",
                        "publishedAt": "2023-05-22T11:00:00Z"
                    }
                ]
            }

            # Mock search news method
            self.mock_news_client.search_news.return_value = {
                "status": "ok",
                "totalResults": 2,
                "articles": [
                    {
                        "source": {"id": "test", "name": "Test News"},
                        "title": "Test Search Result",
                        "description": "This is a test search result",
                        "url": "https://example.com/news/3",
                        "urlToImage": "https://example.com/image3.jpg",
                        "publishedAt": "2023-05-22T10:00:00Z"
                    },
                    {
                        "source": {"id": "test2", "name": "Test News 2"},
                        "title": "Another Search Result",
                        "description": "This is another test search result",
                        "url": "https://example.com/news/4",
                        "urlToImage": "https://example.com/image4.jpg",
                        "publishedAt": "2023-05-22T09:00:00Z"
                    }
                ]
            }

            # Import the News commands
            from bot.features.news.commands import NewsCommands
            self.news_commands = NewsCommands(self.bot)

    async def test_news_command(self):
        """Test the news command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.news_commands.news_command.callback

        # Call the callback directly
        await callback(self.news_commands, interaction, "business", "us", "test")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the News client was called correctly
        self.mock_news_client.get_top_headlines.assert_called_once_with(
            country="us",
            category="business",
            query="test",
            page_size=5
        )

    async def test_news_search_command(self):
        """Test the news search command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.news_commands.news_search_command.callback

        # Call the callback directly
        await callback(self.news_commands, interaction, "test query", "en", "publishedAt")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the News client was called correctly
        self.mock_news_client.search_news.assert_called_once_with(
            query="test query",
            language="en",
            sort_by="publishedAt",
            page_size=5
        )

class TestCurrencyCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Currency commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Import and patch the Currency client
        with patch('bot.features.currency.api.CurrencyClient') as mock_client_class:
            # Set up the mock client
            self.mock_currency_client = mock_client_class.return_value
            self.mock_currency_client.initialized = True

            # Mock convert currency method
            self.mock_currency_client.convert_currency.return_value = {
                "success": True,
                "query": {
                    "from": "USD",
                    "to": "EUR",
                    "amount": 100
                },
                "info": {
                    "timestamp": 1684771200,
                    "rate": 0.92
                },
                "result": 92.0
            }

            # Mock latest rates method
            self.mock_currency_client.get_latest_rates.return_value = {
                "success": True,
                "timestamp": 1684771200,
                "base": "USD",
                "rates": {
                    "EUR": 0.92,
                    "GBP": 0.79,
                    "JPY": 109.25,
                    "CAD": 1.35,
                    "AUD": 1.48
                }
            }

            # Import the Currency commands
            from bot.features.currency.commands import CurrencyCommands
            self.currency_commands = CurrencyCommands(self.bot)

    async def test_convert_command(self):
        """Test the convert command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.currency_commands.convert_command.callback

        # Call the callback directly
        await callback(self.currency_commands, interaction, 100, "USD", "EUR")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Currency client was called correctly
        self.mock_currency_client.convert_currency.assert_called_once_with(
            from_currency="USD",
            to_currency="EUR",
            amount=100
        )

    async def test_exchange_rates_command(self):
        """Test the exchange rates command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.currency_commands.exchange_rates_command.callback

        # Call the callback directly
        await callback(self.currency_commands, interaction, "USD")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Currency client was called correctly
        self.mock_currency_client.get_latest_rates.assert_called_once_with(base_currency="USD")

if __name__ == "__main__":
    unittest.main()
