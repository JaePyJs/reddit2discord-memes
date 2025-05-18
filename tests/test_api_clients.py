"""
Test script for API clients.

This script tests the functionality of the API clients directly.
"""

import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from dotenv import load_dotenv

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

class TestMapsClient(unittest.IsolatedAsyncioTestCase):
    """Test cases for Maps client"""
    
    async def asyncSetUp(self):
        """Set up the test case"""
        # Import and patch the Maps client
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
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
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Import the Maps client
            from bot.features.maps.api import MapsClient
            self.maps_client = MapsClient()
            self.maps_client.api_key = "test_api_key"
            self.maps_client.initialized = True
    
    async def test_geocode(self):
        """Test the geocode method"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
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
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Call the method
            result = await self.maps_client.geocode("New York")
            
            # Check the result
            self.assertEqual(result["status"], "OK")
            self.assertEqual(result["results"][0]["formatted_address"], "New York, NY, USA")
            
            # Check that the API was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(kwargs["params"]["address"], "New York")
            self.assertEqual(kwargs["params"]["key"], "test_api_key")

class TestNewsClient(unittest.IsolatedAsyncioTestCase):
    """Test cases for News client"""
    
    async def asyncSetUp(self):
        """Set up the test case"""
        # Import and patch the News client
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
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
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Import the News client
            from bot.features.news.api import NewsClient
            self.news_client = NewsClient()
            self.news_client.api_key = "test_api_key"
            self.news_client.initialized = True
    
    async def test_get_top_headlines(self):
        """Test the get_top_headlines method"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
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
                    }
                ]
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Call the method
            result = await self.news_client.get_top_headlines(country="us", category="business", query="test")
            
            # Check the result
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["totalResults"], 2)
            self.assertEqual(result["articles"][0]["title"], "Test Headline")
            
            # Check that the API was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(kwargs["params"]["country"], "us")
            self.assertEqual(kwargs["params"]["category"], "business")
            self.assertEqual(kwargs["params"]["q"], "test")
            self.assertEqual(kwargs["headers"]["X-Api-Key"], "test_api_key")

class TestCurrencyClient(unittest.IsolatedAsyncioTestCase):
    """Test cases for Currency client"""
    
    async def asyncSetUp(self):
        """Set up the test case"""
        # Import and patch the Currency client
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "timestamp": 1684771200,
                "base": "USD",
                "rates": {
                    "EUR": 0.92,
                    "GBP": 0.79,
                    "JPY": 109.25
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Import the Currency client
            from bot.features.currency.api import CurrencyClient
            self.currency_client = CurrencyClient()
            self.currency_client.api_key = "test_api_key"
            self.currency_client.initialized = True
    
    async def test_get_latest_rates(self):
        """Test the get_latest_rates method"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Set up the mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "success": True,
                "timestamp": 1684771200,
                "base": "USD",
                "rates": {
                    "EUR": 0.92,
                    "GBP": 0.79,
                    "JPY": 109.25
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Call the method
            result = await self.currency_client.get_latest_rates(base_currency="USD")
            
            # Check the result
            self.assertEqual(result["success"], True)
            self.assertEqual(result["base"], "USD")
            self.assertEqual(result["rates"]["EUR"], 0.92)
            
            # Check that the API was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(kwargs["params"]["access_key"], "test_api_key")
            self.assertEqual(kwargs["params"]["base"], "USD")

if __name__ == "__main__":
    unittest.main()
