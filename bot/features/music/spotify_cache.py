"""
Spotify Cache System

This module provides caching functionality for Spotify API requests to reduce
API calls and improve performance.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

from bot.core.config import CACHE_DIR, DB_PATH

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, 'spotify'), exist_ok=True)

# Cache expiration times (in seconds)
TRACK_CACHE_EXPIRY = 60 * 60 * 24 * 7  # 7 days
ALBUM_CACHE_EXPIRY = 60 * 60 * 24 * 7  # 7 days
PLAYLIST_CACHE_EXPIRY = 60 * 60 * 24 * 1  # 1 day
SEARCH_CACHE_EXPIRY = 60 * 60 * 24 * 1  # 1 day
ARTIST_CACHE_EXPIRY = 60 * 60 * 24 * 7  # 7 days
RECOMMENDATIONS_CACHE_EXPIRY = 60 * 60 * 6  # 6 hours

class SpotifyCache:
    """Cache system for Spotify API requests"""

    def __init__(self):
        """Initialize the Spotify cache system"""
        self._setup_db()

    def _setup_db(self):
        """Set up the Spotify cache table in the database"""
        try:
            # Ensure the database directory exists
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Create Spotify cache table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS spotify_cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                expiry INTEGER NOT NULL
            )
            ''')

            conn.commit()
            conn.close()
            logging.info("Spotify cache database table initialized")
        except Exception as e:
            logging.error(f"Error setting up Spotify cache database: {e}")

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get a cached item

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found or expired
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            SELECT data, expiry FROM spotify_cache
            WHERE cache_key = ?
            ''', (cache_key,))

            result = cursor.fetchone()
            conn.close()

            if result:
                data_json, expiry = result

                # Check if expired
                if expiry < int(time.time()):
                    self.delete(cache_key)
                    return None

                return json.loads(data_json)

            return None
        except Exception as e:
            logging.error(f"Error getting cached item: {e}")
            return None

    def set(self, cache_key: str, data: Any, expiry_seconds: Optional[int] = None) -> bool:
        """
        Set a cached item

        Args:
            cache_key: Cache key
            data: Data to cache
            expiry_seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine expiry based on cache key type
            if expiry_seconds is None:
                if cache_key.startswith('track:'):
                    expiry_seconds = TRACK_CACHE_EXPIRY
                elif cache_key.startswith('album:'):
                    expiry_seconds = ALBUM_CACHE_EXPIRY
                elif cache_key.startswith('playlist:'):
                    expiry_seconds = PLAYLIST_CACHE_EXPIRY
                elif cache_key.startswith('search:'):
                    expiry_seconds = SEARCH_CACHE_EXPIRY
                elif cache_key.startswith('artist:'):
                    expiry_seconds = ARTIST_CACHE_EXPIRY
                elif cache_key.startswith('recommendations:'):
                    expiry_seconds = RECOMMENDATIONS_CACHE_EXPIRY
                else:
                    expiry_seconds = 60 * 60 * 24  # Default: 1 day

            expiry = int(time.time()) + expiry_seconds
            data_json = json.dumps(data)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            INSERT OR REPLACE INTO spotify_cache (cache_key, data, expiry)
            VALUES (?, ?, ?)
            ''', (cache_key, data_json, expiry))

            conn.commit()
            conn.close()

            return True
        except Exception as e:
            logging.error(f"Error setting cached item: {e}")
            return False

    def delete(self, cache_key: str) -> bool:
        """
        Delete a cached item

        Args:
            cache_key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            DELETE FROM spotify_cache
            WHERE cache_key = ?
            ''', (cache_key,))

            conn.commit()
            conn.close()

            return True
        except Exception as e:
            logging.error(f"Error deleting cached item: {e}")
            return False

    def clear_expired(self) -> int:
        """
        Clear all expired cache items

        Returns:
            Number of items cleared
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            DELETE FROM spotify_cache
            WHERE expiry < ?
            ''', (int(time.time()),))

            cleared_count = cursor.rowcount
            conn.commit()
            conn.close()

            return cleared_count
        except Exception as e:
            logging.error(f"Error clearing expired cache items: {e}")
            return 0

    def clear_all(self) -> bool:
        """
        Clear all cache items

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
            DELETE FROM spotify_cache
            ''')

            conn.commit()
            conn.close()

            return True
        except Exception as e:
            logging.error(f"Error clearing all cache items: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Get total count
            cursor.execute('''
            SELECT COUNT(*) FROM spotify_cache
            ''')
            total_count = cursor.fetchone()[0]

            # Get expired count
            cursor.execute('''
            SELECT COUNT(*) FROM spotify_cache
            WHERE expiry < ?
            ''', (int(time.time()),))
            expired_count = cursor.fetchone()[0]

            # Get counts by type
            type_counts = {}
            for prefix in ['track:', 'album:', 'playlist:', 'search:', 'artist:', 'recommendations:']:
                cursor.execute('''
                SELECT COUNT(*) FROM spotify_cache
                WHERE cache_key LIKE ?
                ''', (f'{prefix}%',))
                type_counts[prefix.rstrip(':')] = cursor.fetchone()[0]

            conn.close()

            return {
                'total_count': total_count,
                'expired_count': expired_count,
                'valid_count': total_count - expired_count,
                'type_counts': type_counts
            }
        except Exception as e:
            logging.error(f"Error getting cache statistics: {e}")
            return {
                'total_count': 0,
                'expired_count': 0,
                'valid_count': 0,
                'type_counts': {}
            }
