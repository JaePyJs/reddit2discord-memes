"""
Test script for Weather commands.

This script tests the functionality of the Weather commands.
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

class TestWeatherCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for Weather commands"""

    async def asyncSetUp(self):
        """Set up the test case"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.user = MagicMock()
        self.bot.user.name = "TestBot"

        # Mock the analytics module
        patcher = patch('bot.features.weather.commands.analytics')
        self.mock_analytics = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Import and patch the Weather client
        patcher = patch('bot.features.weather.commands.WeatherClient')
        self.mock_weather_client_class = patcher.start()
        self.addAsyncCleanup(patcher.stop)

        # Create a mock instance
        self.mock_weather_client = MagicMock()
        self.mock_weather_client.initialized = True
        self.mock_weather_client_class.return_value = self.mock_weather_client

        # Mock get_current_weather method
        self.mock_weather_client.get_current_weather = AsyncMock(return_value={
            "coord": {"lon": -0.1257, "lat": 51.5085},
            "weather": [
                {
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01d"
                }
            ],
            "base": "stations",
            "main": {
                "temp": 15.5,
                "feels_like": 14.8,
                "temp_min": 14.0,
                "temp_max": 17.2,
                "pressure": 1020,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {
                "speed": 3.6,
                "deg": 250
            },
            "clouds": {
                "all": 0
            },
            "dt": 1620000000,
            "sys": {
                "type": 2,
                "id": 2019646,
                "country": "GB",
                "sunrise": 1619999999,
                "sunset": 1620050000
            },
            "timezone": 3600,
            "id": 2643743,
            "name": "London",
            "cod": 200
        })

        # Mock get_forecast method
        self.mock_weather_client.get_forecast = AsyncMock(return_value={
            "cod": "200",
            "message": 0,
            "cnt": 40,
            "list": [
                {
                    "dt": 1620021600,
                    "main": {
                        "temp": 16.5,
                        "feels_like": 15.8,
                        "temp_min": 15.0,
                        "temp_max": 18.2,
                        "pressure": 1020,
                        "humidity": 60
                    },
                    "weather": [
                        {
                            "id": 800,
                            "main": "Clear",
                            "description": "clear sky",
                            "icon": "01d"
                        }
                    ],
                    "clouds": {"all": 0},
                    "wind": {"speed": 3.8, "deg": 255},
                    "visibility": 10000,
                    "pop": 0,
                    "sys": {"pod": "d"},
                    "dt_txt": "2023-05-03 12:00:00"
                },
                {
                    "dt": 1620032400,
                    "main": {
                        "temp": 14.5,
                        "feels_like": 13.8,
                        "temp_min": 13.0,
                        "temp_max": 16.2,
                        "pressure": 1022,
                        "humidity": 70
                    },
                    "weather": [
                        {
                            "id": 801,
                            "main": "Clouds",
                            "description": "few clouds",
                            "icon": "02n"
                        }
                    ],
                    "clouds": {"all": 20},
                    "wind": {"speed": 2.8, "deg": 245},
                    "visibility": 10000,
                    "pop": 0,
                    "sys": {"pod": "n"},
                    "dt_txt": "2023-05-03 15:00:00"
                }
            ],
            "city": {
                "id": 2643743,
                "name": "London",
                "coord": {"lat": 51.5085, "lon": -0.1257},
                "country": "GB",
                "population": 1000000,
                "timezone": 3600,
                "sunrise": 1619999999,
                "sunset": 1620050000
            }
        })

        # Mock format methods
        self.mock_weather_client.format_temperature = MagicMock(return_value="15.5°C")
        self.mock_weather_client.format_wind_speed = MagicMock(return_value="3.6 m/s")
        self.mock_weather_client.format_datetime = MagicMock(return_value="12:00")
        self.mock_weather_client.get_weather_icon_url = MagicMock(return_value="https://example.com/icon.png")

        # Import the Weather commands
        from bot.features.weather.commands import WeatherCommands
        self.weather_commands = WeatherCommands(self.bot)

    async def test_weather_command(self):
        """Test the weather command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.weather_commands.weather_command.callback

        # Call the callback directly
        await callback(self.weather_commands, interaction, "London")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Weather client was called correctly
        self.mock_weather_client.get_current_weather.assert_called_once_with("London", "metric")

    async def test_weather_command_error(self):
        """Test the weather command with an error"""
        interaction = MockInteraction()

        # Mock an error
        self.mock_weather_client.get_current_weather.side_effect = Exception("City not found")

        # Get the callback function from the command
        callback = self.weather_commands.weather_command.callback

        # Call the callback directly
        await callback(self.weather_commands, interaction, "NonexistentCity")

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

    async def test_forecast_command(self):
        """Test the forecast command"""
        interaction = MockInteraction()

        # Get the callback function from the command
        callback = self.weather_commands.forecast_command.callback

        # Call the callback directly
        await callback(self.weather_commands, interaction, "London")

        # Check that the command responded
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

        # Check that the Weather client was called correctly
        self.mock_weather_client.get_forecast.assert_called_once_with("London", 3, "metric")

    async def test_forecast_command_error(self):
        """Test the forecast command with an error"""
        interaction = MockInteraction()

        # Mock an error
        self.mock_weather_client.get_forecast.side_effect = Exception("City not found")

        # Get the callback function from the command
        callback = self.weather_commands.forecast_command.callback

        # Call the callback directly
        await callback(self.weather_commands, interaction, "NonexistentCity")

        # Check that the command responded with an error
        interaction.response.defer.assert_called_once()
        interaction.followup.send.assert_called_once()

if __name__ == "__main__":
    unittest.main()
