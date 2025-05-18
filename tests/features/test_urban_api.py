"""
Tests for the Urban Dictionary API functionality.
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

from bot.features.urban.api import UrbanDictionaryClient, UrbanDictionaryAPIError

class TestUrbanDictionaryAPI(unittest.TestCase):
    """Test cases for the UrbanDictionaryClient class"""

    def setUp(self):
        """Set up test environment"""
        # Create a patch for the analytics module
        self.analytics_patcher = patch('bot.features.urban.api.analytics')
        self.analytics_mock = self.analytics_patcher.start()

        # Create a patch for the performance_monitor module
        self.perf_monitor_patcher = patch('bot.features.urban.api.performance_monitor')
        self.perf_monitor_mock = self.perf_monitor_patcher.start()

        # Create the client instance
        self.client = UrbanDictionaryClient()

        # Sample test data
        self.test_definition = {
            "definition": "A test definition with [bracketed] words.",
            "permalink": "https://www.urbandictionary.com/define.php?term=test",
            "thumbs_up": 100,
            "sound_urls": [],
            "author": "Test Author",
            "word": "test",
            "defid": 12345,
            "current_vote": "",
            "written_on": "2020-01-01T00:00:00.000Z",
            "example": "This is a [test] example.",
            "thumbs_down": 10
        }

    def tearDown(self):
        """Clean up after tests"""
        # Stop the patchers
        self.analytics_patcher.stop()
        self.perf_monitor_patcher.stop()

    def test_initialization(self):
        """Test client initialization"""
        # Check that the client is initialized correctly
        self.assertTrue(self.client.initialized)
        self.assertEqual(self.client.base_url, "https://api.urbandictionary.com/v0")

    def test_clean_text(self):
        """Test cleaning text from Urban Dictionary"""
        # Test text with brackets
        text = "This is a [test] with [multiple] bracketed [words]."
        cleaned = self.client._clean_text(text)

        # Check that brackets are replaced with bold formatting
        self.assertEqual(cleaned, "This is a **test** with **multiple** bracketed **words**.")

        # Test text with newlines
        text = "Line 1\\r\\nLine 2\\nLine 3"
        cleaned = self.client._clean_text(text)

        # Check that newlines are replaced correctly
        self.assertEqual(cleaned, "Line 1\nLine 2\nLine 3")

        # Test long text
        text = "a" * 1500
        cleaned = self.client._clean_text(text)

        # Check that the text is truncated
        self.assertEqual(len(cleaned), 1000)
        self.assertTrue(cleaned.endswith("..."))

    def test_format_definition(self):
        """Test formatting a definition for display"""
        # Format the test definition
        formatted = self.client.format_definition(self.test_definition)

        # Check that the formatting is correct
        self.assertTrue(formatted.startswith("**test**"))
        self.assertIn("A test definition with **bracketed** words.", formatted)
        self.assertIn("*Example:*", formatted)
        self.assertIn("This is a **test** example.", formatted)
        self.assertIn("👍 100 | 👎 10 | by Test Author", formatted)

    @patch('aiohttp.ClientSession.get')
    async def test_define(self, mock_get):
        """Test defining a term"""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "list": [self.test_definition]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Define a term
        results = await self.client.define("test")

        # Check that the results are correct
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_definition)

        # Check that the API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertEqual(call_args, "https://api.urbandictionary.com/v0/define")

        # Check that analytics was called
        self.analytics_mock.track_api_call.assert_called()

    @patch('aiohttp.ClientSession.get')
    async def test_define_error(self, mock_get):
        """Test error handling when defining a term"""
        # Create a mock response with an error
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Define a term and expect an error
        with self.assertRaises(UrbanDictionaryAPIError):
            await self.client.define("test")

        # Check that analytics was called with error
        self.analytics_mock.track_api_call.assert_called_with(
            "urban_define", False, 0.5, metadata={"error": "Bad Request", "status": 400}
        )

    @patch('aiohttp.ClientSession.get')
    async def test_random(self, mock_get):
        """Test getting random definitions"""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "list": [self.test_definition]
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        # Set up performance monitor mock
        self.perf_monitor_mock.start_timer.return_value = "test_timer"
        self.perf_monitor_mock.stop_timer.return_value = 0.5

        # Get random definitions
        results = await self.client.random()

        # Check that the results are correct
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_definition)

        # Check that the API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        self.assertEqual(call_args, "https://api.urbandictionary.com/v0/random")

        # Check that analytics was called
        self.analytics_mock.track_api_call.assert_called()

if __name__ == '__main__':
    # Run the async tests
    loop = asyncio.get_event_loop()
    unittest.main()
