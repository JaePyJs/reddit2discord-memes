import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import re
import requests
import json
import os
import time
import asyncio
from typing import Dict, List, Optional, Any, Union
from bot.core.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, CACHE_DIR
from bot.core.analytics import analytics
from bot.core.performance_monitor import performance_monitor, timed
from bot.features.music.spotify_cache import SpotifyCache
from bot.utils.secure_logging import get_secure_logger

# Use secure logger instead of standard logging
secure_logger = get_secure_logger(__name__)

class SpotifyClient:
    """Enhanced client for interacting with the Spotify API"""
    def __init__(self):
        self.cache = SpotifyCache()
        try:
            # Log the credentials we're using (without showing full secret)
            client_id = SPOTIFY_CLIENT_ID
            client_secret = SPOTIFY_CLIENT_SECRET

            if not client_id or not client_secret:
                secure_logger.error("Spotify credentials are missing. Make sure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are set in .env")
                self.initialized = False
                return

            # Log partial credentials for debugging
            secure_logger.info(f"Initializing Spotify client with ID: {client_id[:5]}...{client_id[-5:]} and Secret: {client_secret[:3]}...{client_secret[-3:]}")

            self.client_credentials_manager = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)

            # Test the connection
            self.spotify.search(q='test', limit=1)

            self.initialized = True
            secure_logger.info("Spotify client successfully initialized")
        except Exception as e:
            secure_logger.error(f"Failed to initialize Spotify client: {e}")
            self.initialized = False

    def _extract_id_from_url(self, url):
        """Extract ID from Spotify URL"""
        # Extract track/playlist/album ID from URL
        if not url:
            raise ValueError("No URL provided")

        # Try to find the ID using regex pattern
        pattern = r'https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'
        match = re.match(pattern, url)

        if not match:
            raise ValueError(f"Invalid Spotify URL format: {url}")

        return match.group(1), match.group(2)  # Return type and ID

    @timed(operation_type="spotify_api")
    async def get_track(self, url):
        """Get information about a Spotify track with enhanced metadata"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")

        # Check cache first
        cache_key = f"track:{url}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            analytics.track_feature("spotify_track_cache_hit", "system")
            return cached_data

        # Track API usage
        analytics.track_feature("spotify_track_api_call", "system")

        try:
            # Extract track ID from URL
            content_type, track_id = self._extract_id_from_url(url)
            if content_type != "track":
                raise ValueError(f"URL is not a Spotify track: {url}")

            # Get track info from Spotify API
            track_info = self.spotify.track(track_id)

            # Extract relevant information
            result = {
                'title': track_info['name'],
                'artist': ", ".join([artist['name'] for artist in track_info['artists']]),
                'album': track_info['album']['name'],
                'release_date': track_info['album'].get('release_date', 'Unknown'),
                'duration_ms': track_info['duration_ms'],
                'popularity': track_info['popularity'],
                'explicit': track_info['explicit'],
                'search_query': f"{track_info['name']} {track_info['artists'][0]['name']} audio",
                'album_art': track_info['album']['images'][0]['url'] if track_info['album']['images'] else None,
                'preview_url': track_info.get('preview_url'),
                'external_urls': track_info['external_urls'],
                'uri': track_info['uri']
            }

            # Cache the result
            self.cache.set(cache_key, result)

            return result
        except Exception as e:
            secure_logger.error(f"Error processing Spotify track URL {url}: {e}")
            # Create a fallback search query using the URL itself
            return {
                'title': f"Spotify Track",
                'artist': "Unknown Artist",
                'album': "Unknown Album",
                'search_query': f"spotify track {url.split('/')[-1].split('?')[0]} audio",
                'album_art': None
            }

    @timed(operation_type="spotify_api")
    async def get_playlist_tracks(self, url, limit=50, offset=0):
        """Get tracks from a Spotify playlist with pagination support"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")

        # Check cache first
        cache_key = f"playlist:{url}:{limit}:{offset}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            analytics.track_feature("spotify_playlist_cache_hit", "system")
            return cached_data

        # Track API usage
        analytics.track_feature("spotify_playlist_api_call", "system", metadata={"limit": limit, "offset": offset})

        try:
            content_type, playlist_id = self._extract_id_from_url(url)
            if content_type != "playlist":
                raise ValueError(f"URL is not a Spotify playlist: {url}")

            # Extract playlist name from URL for fallback
            playlist_name = f"Playlist {playlist_id}"
            try:
                # Try to get the playlist name from the URL path
                path_parts = url.split('/')
                if len(path_parts) > 5:  # URL might contain the name
                    playlist_name = path_parts[5].split('?')[0].replace('-', ' ').title()
            except:
                pass

            try:
                # Get playlist info from Spotify API
                playlist_info = self.spotify.playlist(playlist_id)
                playlist_name = playlist_info['name']
                playlist_owner = playlist_info['owner']['display_name']

                # Get tracks with pagination
                results = self.spotify.playlist_items(
                    playlist_id,
                    offset=offset,
                    limit=limit,
                    fields='items.track(name,artists,album(name,images),duration_ms,preview_url,external_urls)'
                )

                tracks = []
                for item in results['items']:
                    if not item['track']:
                        continue

                    track = item['track']
                    artist_name = ", ".join([artist['name'] for artist in track['artists']])
                    album_art = track['album']['images'][0]['url'] if track['album']['images'] else None

                    tracks.append({
                        'title': track['name'],
                        'artist': artist_name,
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'search_query': f"{track['name']} {artist_name} audio",
                        'album_art': album_art,
                        'preview_url': track.get('preview_url'),
                        'external_urls': track['external_urls']
                    })

                result = {
                    'playlist_name': playlist_name,
                    'playlist_owner': playlist_owner,
                    'tracks': tracks,
                    'total_tracks': playlist_info['tracks']['total'],
                    'current_offset': offset,
                    'limit': limit
                }

                # Cache the result
                self.cache.set(cache_key, result)

                return result
            except Exception as api_error:
                secure_logger.error(f"Error accessing Spotify API for playlist {playlist_id}: {api_error}")
                # Fall back to a web scraping approach or use a generic search

                # Create a search query based on the playlist name
                search_query = f"{playlist_name} playlist music"

                # Create a fallback track for the playlist
                tracks = [{
                    'title': f"{playlist_name}",
                    'artist': "Spotify Playlist",
                    'album': "Spotify",
                    'duration_ms': 0,
                    'search_query': search_query,
                    'album_art': None,
                    'preview_url': None,
                    'external_urls': {'spotify': url}
                }]

                # Try to get more specific tracks if we can identify the genre or theme
                if "j-pop" in url.lower() or "jpop" in url.lower():
                    tracks.append({
                        'title': "J-Pop Mix",
                        'artist': "Various Artists",
                        'album': "J-Pop Hits",
                        'duration_ms': 0,
                        'search_query': "j-pop hits playlist music",
                        'album_art': None,
                        'preview_url': None,
                        'external_urls': {'spotify': url}
                    })

                result = {
                    'playlist_name': playlist_name,
                    'playlist_owner': "Spotify",
                    'tracks': tracks,
                    'total_tracks': len(tracks),
                    'current_offset': 0,
                    'limit': limit
                }

                # Cache the result (but with shorter expiry)
                self.cache.set(cache_key, result, expiry_seconds=60*60)  # 1 hour

                return result

        except Exception as e:
            secure_logger.error(f"Error processing Spotify playlist URL {url}: {e}")
            # Create a fallback result with a more specific search query
            playlist_id = url.split('/')[-1].split('?')[0]

            # Try to extract genre/theme from URL or playlist ID
            playlist_theme = "popular"

            # Check for common genres in the URL
            if "j-pop" in url.lower() or "jpop" in url.lower():
                playlist_theme = "j-pop"
                search_query = "j-pop hits popular songs playlist"
            elif "k-pop" in url.lower() or "kpop" in url.lower():
                playlist_theme = "k-pop"
                search_query = "k-pop hits popular songs playlist"
            elif "rock" in url.lower():
                playlist_theme = "rock"
                search_query = "rock hits popular songs playlist"
            elif "hip-hop" in url.lower() or "hiphop" in url.lower() or "rap" in url.lower():
                playlist_theme = "hip hop"
                search_query = "hip hop rap hits popular songs playlist"
            elif "pop" in url.lower():
                playlist_theme = "pop"
                search_query = "pop hits popular songs playlist"
            elif "edm" in url.lower() or "electronic" in url.lower():
                playlist_theme = "electronic"
                search_query = "electronic edm hits popular songs playlist"
            elif "country" in url.lower():
                playlist_theme = "country"
                search_query = "country hits popular songs playlist"
            elif "jazz" in url.lower():
                playlist_theme = "jazz"
                search_query = "jazz classics popular songs playlist"
            elif "classical" in url.lower():
                playlist_theme = "classical"
                search_query = "classical music popular pieces playlist"
            else:
                # Default to a generic popular music search
                search_query = "popular music hits playlist 2024"

            # Create multiple tracks for better chances of finding something playable
            tracks = [
                {
                    'title': f"{playlist_theme.title()} Playlist",
                    'artist': "Various Artists",
                    'album': "Spotify Playlist",
                    'duration_ms': 0,
                    'search_query': search_query,
                    'album_art': None,
                    'preview_url': None,
                    'external_urls': {'spotify': url}
                },
                {
                    'title': f"{playlist_theme.title()} Mix",
                    'artist': "Top Artists",
                    'album': "Popular Hits",
                    'duration_ms': 0,
                    'search_query': f"{playlist_theme} top hits mix",
                    'album_art': None,
                    'preview_url': None,
                    'external_urls': {'spotify': url}
                },
                {
                    'title': "Popular Music Mix",
                    'artist': "Various Artists",
                    'album': "Top Charts",
                    'duration_ms': 0,
                    'search_query': "popular music hits 2024",
                    'album_art': None,
                    'preview_url': None,
                    'external_urls': {'spotify': url}
                }
            ]

            return {
                'playlist_name': f"{playlist_theme.title()} Playlist",
                'playlist_owner': "Spotify",
                'tracks': tracks,
                'total_tracks': len(tracks),
                'current_offset': 0,
                'limit': limit
            }

    @timed(operation_type="spotify_api")
    async def get_album_tracks(self, url, limit=50, offset=0):
        """Get tracks from a Spotify album with pagination support"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")

        # Check cache first
        cache_key = f"album:{url}:{limit}:{offset}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            analytics.track_feature("spotify_album_cache_hit", "system")
            return cached_data

        # Track API usage
        analytics.track_feature("spotify_album_api_call", "system", metadata={"limit": limit, "offset": offset})

        try:
            content_type, album_id = self._extract_id_from_url(url)
            if content_type != "album":
                raise ValueError(f"URL is not a Spotify album: {url}")

            # Get album info from Spotify API
            album_info = self.spotify.album(album_id)
            album_name = album_info['name']
            artist_name = ", ".join([artist['name'] for artist in album_info['artists']])
            album_art = album_info['images'][0]['url'] if album_info['images'] else None

            # Get tracks with pagination
            results = self.spotify.album_tracks(
                album_id,
                offset=offset,
                limit=limit
            )

            tracks = []
            for track in results['items']:
                track_artist = ", ".join([artist['name'] for artist in track['artists']])

                tracks.append({
                    'title': track['name'],
                    'artist': track_artist,
                    'album': album_name,
                    'duration_ms': track['duration_ms'],
                    'search_query': f"{track['name']} {track_artist} audio",
                    'album_art': album_art,
                    'preview_url': track.get('preview_url'),
                    'external_urls': track['external_urls']
                })

            result = {
                'album_name': album_name,
                'album_artist': artist_name,
                'tracks': tracks,
                'total_tracks': album_info['total_tracks'],
                'current_offset': offset,
                'limit': limit,
                'album_art': album_art,
                'release_date': album_info.get('release_date', 'Unknown')
            }

            # Cache the result
            self.cache.set(cache_key, result)

            return result
        except Exception as e:
            secure_logger.error(f"Error processing Spotify album URL {url}: {e}")
            # Create a fallback result
            return {
                'album_name': "Unknown Album",
                'album_artist': "Unknown Artist",
                'tracks': [{
                    'title': "Spotify Album",
                    'artist': "Unknown Artist",
                    'search_query': f"spotify album {url.split('/')[-1].split('?')[0]} music audio",
                    'album_art': None
                }],
                'total_tracks': 1,
                'current_offset': 0,
                'limit': limit
            }

    @timed(operation_type="spotify_api")
    async def get_recommendations(self, track_url=None, artist_ids=None, genre_seeds=None, limit=5):
        """Get track recommendations based on a track, artists, or genres"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")

        # Check cache first
        cache_key = f"recommendations:{track_url}:{artist_ids}:{genre_seeds}:{limit}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            analytics.track_feature("spotify_recommendations_cache_hit", "system")
            return cached_data

        # Track API usage
        analytics.track_feature("spotify_recommendations_api_call", "system",
                               metadata={"track_url": track_url is not None,
                                        "artist_count": len(artist_ids) if artist_ids else 0,
                                        "genre_count": len(genre_seeds) if genre_seeds else 0})

        try:
            seed_tracks = []
            seed_artists = artist_ids or []
            seed_genres = genre_seeds or []

            # If track URL is provided, extract track ID
            if track_url:
                content_type, track_id = self._extract_id_from_url(track_url)
                if content_type == "track":
                    seed_tracks.append(track_id)

                    # If no artist IDs provided, get artists from the track
                    if not artist_ids:
                        track_info = self.spotify.track(track_id)
                        for artist in track_info['artists'][:2]:  # Limit to 2 artists
                            seed_artists.append(artist['id'])

            # Get recommendations from Spotify API
            recommendations = self.spotify.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=limit
            )

            tracks = []
            for track in recommendations['tracks']:
                artist_name = ", ".join([artist['name'] for artist in track['artists']])
                album_art = track['album']['images'][0]['url'] if track['album']['images'] else None

                tracks.append({
                    'title': track['name'],
                    'artist': artist_name,
                    'album': track['album']['name'],
                    'duration_ms': track['duration_ms'],
                    'search_query': f"{track['name']} {artist_name} audio",
                    'album_art': album_art,
                    'preview_url': track.get('preview_url'),
                    'external_urls': track['external_urls'],
                    'uri': track['uri']
                })

            result = {
                'tracks': tracks,
                'seed_tracks': seed_tracks,
                'seed_artists': seed_artists,
                'seed_genres': seed_genres
            }

            # Cache the result
            self.cache.set(cache_key, result)

            return result
        except Exception as e:
            secure_logger.error(f"Error getting Spotify recommendations: {e}")
            return {
                'tracks': [],
                'seed_tracks': [],
                'seed_artists': [],
                'seed_genres': []
            }

    @timed(operation_type="spotify_api")
    async def parse_spotify_url(self, url):
        """Parse a Spotify URL and return appropriate data"""
        try:
            if not self.initialized:
                secure_logger.error("Cannot parse Spotify URL: Spotify client not initialized")
                raise Exception("Spotify client not initialized. Check your credentials.")

            secure_logger.info(f"Parsing Spotify URL: {url}")

            # Track the URL type for analytics
            url_type = "unknown"
            if "track" in url:
                url_type = "track"
                secure_logger.info("Detected Spotify track URL")
                result = await self.get_track(url)
            elif "playlist" in url:
                url_type = "playlist"
                secure_logger.info("Detected Spotify playlist URL")
                playlist_data = await self.get_playlist_tracks(url)
                result = playlist_data['tracks']
            elif "album" in url:
                url_type = "album"
                secure_logger.info("Detected Spotify album URL")
                album_data = await self.get_album_tracks(url)
                result = album_data['tracks']
            else:
                secure_logger.error(f"Unsupported Spotify URL type: {url}")
                analytics.track_error("spotify_unsupported_url", metadata={"url": url})
                raise ValueError(f"Unsupported Spotify URL type: {url}")

            # Track successful parsing
            analytics.track_feature(f"spotify_{url_type}_parsed", "system")
            return result
        except Exception as e:
            secure_logger.error(f"Error parsing Spotify URL {url}: {e}")
            analytics.track_error("spotify_url_parse_error", metadata={"url": url, "error": str(e)})
            raise Exception(f"Error processing Spotify URL: {str(e)}")
