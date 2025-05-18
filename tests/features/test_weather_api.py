"""
Tests for the OpenWeatherMap API functionality.
"""

import unittest
import os
import sys
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create a mock for the analytics module
sys.modules['bot.core.analytics'] = MagicMock()
sys.modules['bot.core.performance_monitor'] = MagicMock()

from bot.features.weather.api import WeatherClient, WeatherAPIError

class TestWeatherAPI(unittest.TestCase):
    """Test cases for the WeatherClient class"""

    def setUp(self):
        """Set up test environment"""
        # Create a patch for the OPENWEATHERMAP_API_KEY constant
        self.api_key_patcher = patch('bot.features.weather.api.OPENWEATHERMAP_API_KEY', 'test_api_key')
        self.api_key_mock = self.api_key_patcher.start()

        # Create a patch for the analytics module
        self.analytics_patcher = patch('bot.features.weather.api.analytics')
        self.analytics_mock = self.analytics_patcher.start()

        # Create a patch for the performance_monitor module
        self.perf_monitor_patcher = patch('bot.features.weather.api.performance_monitor')
        self.perf_monitor_mock = self.perf_monitor_patcher.start()

        # Create the client instance
        self.client = WeatherClient()

        # Sample test data for current weather
        self.test_current_weather = {
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
                "pressure": 1015,
                "humidity": 76
            },
            "visibility": 10000,
            "wind": {
                "speed": 3.6,
                "deg": 240
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
        }

        # Sample test data for forecast
        self.test_forecast = {
            "cod": "200",
            "message": 0,
            "cnt": 40,
            "list": [
                {
                    "dt": 1620000000,
                    "main": {
                        "temp": 15.5,
                        "feels_like": 14.8,
                        "temp_min": 14.0,
                        "temp_max": 17.2,
                        "pressure": 1015,
                        "humidity": 76
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
                    "wind": {"speed": 3.6, "deg": 240},
                    "visibility": 10000,
                    "pop": 0,
                    "sys": {"pod": "d"},
                    "dt_txt": "2023-05-01 12:00:00"
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
        }

    def tearDown(self):
        """Clean up after tests"""
        # Stop the patchers
        self.api_key_patcher.stop()
        self.analytics_patcher.stop()
        self.perf_monitor_patcher.stop()

    def test_initialization(self):
        """Test client initialization"""
        # Check that the client is initialized correctly
        self.assertTrue(self.client.initialized)
        self.assertEqual(self.client.api_key, 'test_api_key')
        self.assertEqual(self.client.base_url, "https://api.openweathermap.org/data/2.5")

    def test_initialization_no_api_key(self):
        """Test client initialization with no API key"""
        # Create a patch for the OPENWEATHERMAP_API_KEY constant with an empty value
        with patch('bot.features.weather.api.OPENWEATHERMAP_API_KEY', ''):
            # Create the client instance
            client = WeatherClient()

            # Check that the client is not initialized
            self.assertFalse(client.initialized)

    def test_get_weather_icon_url(self):
        """Test getting weather icon URL"""
        # Get icon URL
        url = self.client.get_weather_icon_url("01d")

        # Check that the URL is correct
        self.assertEqual(url, "https://openweathermap.org/img/wn/01d@2x.png")

    def test_format_temperature(self):
        """Test formatting temperature"""
        # Test metric units
        temp_metric = self.client.format_temperature(15.5, "metric")
        self.assertEqual(temp_metric, "15.5°C")

        # Test imperial units
        temp_imperial = self.client.format_temperature(59.0, "imperial")
        self.assertEqual(temp_imperial, "59.0°F")

        # Test standard units
        temp_standard = self.client.format_temperature(288.7, "standard")
        self.assertEqual(temp_standard, "288.7K")

    def test_format_wind_speed(self):
        """Test formatting wind speed"""
        # Test metric units
        speed_metric = self.client.format_wind_speed(3.6, "metric")
        self.assertEqual(speed_metric, "3.6 m/s")

        # Test imperial units
        speed_imperial = self.client.format_wind_speed(8.0, "imperial")
        self.assertEqual(speed_imperial, "8.0 mph")

        # Test standard units
        speed_standard = self.client.format_wind_speed(3.6, "standard")
        self.assertEqual(speed_standard, "3.6 m/s")

    def test_format_datetime(self):
        """Test formatting datetime"""
        # Test with default format
        dt = self.client.format_datetime(1620000000)
        self.assertEqual(dt, datetime.fromtimestamp(1620000000).strftime("%Y-%m-%d %H:%M:%S"))

        # Test with custom format
        dt_custom = self.client.format_datetime(1620000000, "%H:%M")
        self.assertEqual(dt_custom, datetime.fromtimestamp(1620000000).strftime("%H:%M"))

    @patch('aiohttp.ClientSession.get')
    async def test_get_current_weather(self, mock_get):
        """Test getting current weather"""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = self.test_current_weather
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Get current weather
        result = await self.client.get_current_weather("London")

        # Check that the result is correct
        self.assertEqual(result, self.test_current_weather)

        # Check that the API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertEqual(call_args, "https://api.openweathermap.org/data/2.5/weather")

        # Check that analytics was called
        self.analytics_mock.track_api_call.assert_called()

    @patch('aiohttp.ClientSession.get')
    async def test_get_forecast(self, mock_get):
        """Test getting weather forecast"""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = self.test_forecast
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Get forecast
        result = await self.client.get_forecast("London", 5)

        # Check that the result is correct
        self.assertEqual(result, self.test_forecast)

        # Check that the API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertEqual(call_args, "https://api.openweathermap.org/data/2.5/forecast")

        # Check that analytics was called
        self.analytics_mock.track_api_call.assert_called()

if __name__ == '__main__':
    # Run the async tests
    loop = asyncio.get_event_loop()
    unittest.main()
