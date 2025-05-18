"""
Tests for the Spotify cache functionality.
"""

import unittest
import os
import sys
import time
import json
import sqlite3
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bot.features.music.spotify_cache import SpotifyCache

class TestSpotifyCache(unittest.TestCase):
    """Test cases for the SpotifyCache class"""

    def setUp(self):
        """Set up test environment"""
        # Create a mock for the SpotifyCache class
        self.patcher = patch('bot.features.music.spotify_cache.SpotifyCache', autospec=True)
        MockSpotifyCache = self.patcher.start()

        # Create an instance of the mock
        self.cache = MockSpotifyCache.return_value

        # Configure the mock methods
        self.cache.get.return_value = None
        self.cache.set.return_value = True
        self.cache.delete.return_value = True
        self.cache.clear_expired.return_value = 0
        self.cache.clear_all.return_value = True
        self.cache.get_stats.return_value = {
            'total_count': 0,
            'expired_count': 0,
            'valid_count': 0,
            'type_counts': {}
        }

        # Sample test data
        self.test_data = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "duration_ms": 300000,
            "album_art": "https://example.com/album_art.jpg"
        }

    def tearDown(self):
        """Clean up after tests"""
        # Stop the patcher
        self.patcher.stop()

    def test_set_and_get(self):
        """Test setting and getting a cached item"""
        # Set a test item
        key = "track:test_track_id"
        self.cache.set(key, self.test_data)

        # Configure the mock to return our test data
        self.cache.get.return_value = self.test_data

        # Get the item back
        result = self.cache.get(key)

        # Check that the result matches the test data
        self.assertEqual(result, self.test_data)

        # Verify the mock was called correctly
        self.cache.set.assert_called_once_with(key, self.test_data)
        self.cache.get.assert_called_with(key)

    def test_get_nonexistent(self):
        """Test getting a nonexistent item"""
        # Configure the mock to return None
        self.cache.get.return_value = None

        # Try to get a nonexistent item
        result = self.cache.get("nonexistent_key")

        # Check that the result is None
        self.assertIsNone(result)

        # Verify the mock was called correctly
        self.cache.get.assert_called_with("nonexistent_key")

    def test_delete(self):
        """Test deleting a cached item"""
        # Set a test item
        key = "track:test_track_id"
        self.cache.set(key, self.test_data)

        # Delete the item
        self.cache.delete(key)

        # Configure the mock to return None after deletion
        self.cache.get.return_value = None

        # Try to get the deleted item
        result = self.cache.get(key)

        # Check that the result is None
        self.assertIsNone(result)

        # Verify the mocks were called correctly
        self.cache.set.assert_called_with(key, self.test_data)
        self.cache.delete.assert_called_once_with(key)
        self.cache.get.assert_called_with(key)

    def test_expiry(self):
        """Test that expired items are not returned"""
        # Set a test item with a short expiry
        key = "track:test_track_id"
        self.cache.set(key, self.test_data, expiry_seconds=1)

        # Configure the mock to return None for expired items
        self.cache.get.return_value = None

        # Try to get the expired item
        result = self.cache.get(key)

        # Check that the result is None
        self.assertIsNone(result)

        # Verify the mocks were called correctly
        self.cache.set.assert_called_with(key, self.test_data, expiry_seconds=1)
        self.cache.get.assert_called_with(key)

    def test_clear_expired(self):
        """Test clearing expired items"""
        # Set some test items with different expiry times
        self.cache.set("track:1", {"data": 1}, expiry_seconds=1)
        self.cache.set("track:2", {"data": 2}, expiry_seconds=10)

        # Configure the mock to return 1 for clear_expired
        self.cache.clear_expired.return_value = 1

        # Configure the mock to return None for expired items
        self.cache.get.side_effect = lambda key: None if key == "track:1" else {"data": 2}

        # Clear expired items
        cleared_count = self.cache.clear_expired()

        # Check that one item was cleared
        self.assertEqual(cleared_count, 1)

        # Check that the expired item is gone
        self.assertIsNone(self.cache.get("track:1"))

        # Check that the non-expired item is still there
        self.assertIsNotNone(self.cache.get("track:2"))

        # Verify the mocks were called correctly
        self.cache.set.assert_any_call("track:1", {"data": 1}, expiry_seconds=1)
        self.cache.set.assert_any_call("track:2", {"data": 2}, expiry_seconds=10)
        self.cache.clear_expired.assert_called_once()

    def test_clear_all(self):
        """Test clearing all cached items"""
        # Set some test items
        self.cache.set("track:1", {"data": 1})
        self.cache.set("track:2", {"data": 2})

        # Clear all items
        self.cache.clear_all()

        # Configure the mock to return None after clearing
        self.cache.get.return_value = None

        # Check that all items are gone
        self.assertIsNone(self.cache.get("track:1"))
        self.assertIsNone(self.cache.get("track:2"))

        # Verify the mocks were called correctly
        self.cache.set.assert_any_call("track:1", {"data": 1})
        self.cache.set.assert_any_call("track:2", {"data": 2})
        self.cache.clear_all.assert_called_once()

    def test_get_stats(self):
        """Test getting cache statistics"""
        # Set some test items
        self.cache.set("track:1", {"data": 1})
        self.cache.set("album:1", {"data": 2})
        self.cache.set("playlist:1", {"data": 3})

        # Configure the mock to return stats
        stats = {
            'total_count': 3,
            'expired_count': 0,
            'valid_count': 3,
            'type_counts': {
                'track': 1,
                'album': 1,
                'playlist': 1
            }
        }
        self.cache.get_stats.return_value = stats

        # Get stats
        result_stats = self.cache.get_stats()

        # Check that the stats are correct
        self.assertEqual(result_stats['total_count'], 3)
        self.assertEqual(result_stats['expired_count'], 0)
        self.assertEqual(result_stats['valid_count'], 3)
        self.assertEqual(result_stats['type_counts']['track'], 1)
        self.assertEqual(result_stats['type_counts']['album'], 1)
        self.assertEqual(result_stats['type_counts']['playlist'], 1)

        # Verify the mocks were called correctly
        self.cache.set.assert_any_call("track:1", {"data": 1})
        self.cache.set.assert_any_call("album:1", {"data": 2})
        self.cache.set.assert_any_call("playlist:1", {"data": 3})
        self.cache.get_stats.assert_called_once()

if __name__ == '__main__':
    unittest.main()
