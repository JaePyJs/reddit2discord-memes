"""
Tests for the Tenor API functionality.
"""

import unittest
import os
import sys
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Create a mock for the analytics module
sys.modules['bot.core.analytics'] = MagicMock()
sys.modules['bot.core.performance_monitor'] = MagicMock()

from bot.features.tenor.api import TenorClient, TenorAPIError

class TestTenorAPI(unittest.TestCase):
    """Test cases for the TenorClient class"""

    def setUp(self):
        """Set up test environment"""
        # Create a patch for the TENOR_API_KEY constant
        self.api_key_patcher = patch('bot.features.tenor.api.TENOR_API_KEY', 'test_api_key')
        self.api_key_mock = self.api_key_patcher.start()

        # Create a patch for the analytics module
        self.analytics_patcher = patch('bot.features.tenor.api.analytics')
        self.analytics_mock = self.analytics_patcher.start()

        # Create a patch for the performance_monitor module
        self.perf_monitor_patcher = patch('bot.features.tenor.api.performance_monitor')
        self.perf_monitor_mock = self.perf_monitor_patcher.start()

        # Create the client instance
        self.client = TenorClient()

        # Sample test data
        self.test_gif_data = {
            "id": "test_id",
            "title": "Test GIF",
            "media_formats": {
                "gif": {
                    "url": "https://example.com/test.gif",
                    "dims": [200, 200],
                    "duration": 0,
                    "size": 12345
                },
                "mp4": {
                    "url": "https://example.com/test.mp4",
                    "dims": [200, 200],
                    "duration": 1.5,
                    "size": 6789
                }
            },
            "created": 1620000000,
            "content_description": "Test description",
            "itemurl": "https://example.com/test",
            "url": "https://tenor.com/test",
            "tags": ["test", "example"],
            "flags": []
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
        self.assertEqual(self.client.base_url, "https://tenor.googleapis.com/v2")

    def test_initialization_no_api_key(self):
        """Test client initialization with no API key"""
        # Create a patch for the TENOR_API_KEY constant with an empty value
        with patch('bot.features.tenor.api.TENOR_API_KEY', ''):
            # Create the client instance
            client = TenorClient()

            # Check that the client is not initialized
            self.assertFalse(client.initialized)

    def test_extract_gif_url(self):
        """Test extracting GIF URL from API response"""
        # Extract GIF URL
        url = self.client.extract_gif_url(self.test_gif_data)

        # Check that the URL is correct
        self.assertEqual(url, "https://example.com/test.gif")

    def test_extract_gif_url_specific_format(self):
        """Test extracting specific format URL from API response"""
        # Extract MP4 URL
        url = self.client.extract_gif_url(self.test_gif_data, "mp4")

        # Check that the URL is correct
        self.assertEqual(url, "https://example.com/test.mp4")

    def test_extract_gif_url_fallback(self):
        """Test fallback when requested format is not available"""
        # Create test data with only MP4 format
        test_data = {
            "media_formats": {
                "mp4": {
                    "url": "https://example.com/test.mp4"
                }
            }
        }

        # Extract GIF URL (which doesn't exist)
        url = self.client.extract_gif_url(test_data, "gif")

        # Check that it falls back to MP4
        self.assertEqual(url, "https://example.com/test.mp4")

    def test_extract_gif_url_no_formats(self):
        """Test when no formats are available"""
        # Create test data with no formats
        test_data = {
            "media_formats": {}
        }

        # Extract GIF URL
        url = self.client.extract_gif_url(test_data)

        # Check that the result is None
        self.assertIsNone(url)

    @patch('aiohttp.ClientSession.get')
    async def test_search_gifs(self, mock_get):
        """Test searching for GIFs"""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "results": [self.test_gif_data]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Search for GIFs
        results = await self.client.search_gifs("test query")

        # Check that the results are correct
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_gif_data)

        # Check that the API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertEqual(call_args, "https://tenor.googleapis.com/v2/search")

        # Check that analytics was called
        self.analytics_mock.track_api_call.assert_called()

    @patch('aiohttp.ClientSession.get')
    async def test_search_gifs_error(self, mock_get):
        """Test error handling when searching for GIFs"""
        # Create a mock response with an error
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Search for GIFs and expect an error
        with self.assertRaises(TenorAPIError):
            await self.client.search_gifs("test query")

        # Check that analytics was called with error
        self.analytics_mock.track_api_call.assert_called_with(
            "tenor_search", False, 0.5, metadata={"error": "Bad Request", "status": 400}
        )

if __name__ == '__main__':
    # Run the async tests
    loop = asyncio.get_event_loop()
    unittest.main()
