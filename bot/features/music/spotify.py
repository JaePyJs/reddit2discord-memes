import spotipy 
from spotipy.oauth2 import SpotifyClientCredentials 
import logging 
import re
import requests
import json
import os
import time
from typing import Dict, List, Optional, Any, Union
from bot.core.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Cache configuration
CACHE_DIR = "data/spotify_cache"
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)
MAX_CACHE_ITEMS = 100  # Maximum number of items to keep in cache

class SpotifyCache:
    """Cache for Spotify data to reduce API calls"""
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache from disk
        self._load_cache()
        
    def _load_cache(self):
        """Load cache from disk"""
        try:
            cache_file = os.path.join(self.cache_dir, "spotify_cache.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    self.memory_cache = json.load(f)
                logging.info(f"Loaded {len(self.memory_cache)} items from Spotify cache")
        except Exception as e:
            logging.error(f"Error loading Spotify cache: {e}")
            self.memory_cache = {}
            
    def _save_cache(self):
        """Save cache to disk"""
        try:
            cache_file = os.path.join(self.cache_dir, "spotify_cache.json")
            with open(cache_file, 'w') as f:
                json.dump(self.memory_cache, f)
        except Exception as e:
            logging.error(f"Error saving Spotify cache: {e}")
            
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item from cache"""
        if key in self.memory_cache:
            item = self.memory_cache[key]
            # Check if item is expired
            if time.time() - item.get('timestamp', 0) < CACHE_EXPIRY:
                logging.info(f"Cache hit for {key}")
                return item.get('data')
            else:
                # Remove expired item
                del self.memory_cache[key]
                self._save_cache()
        return None
        
    def set(self, key: str, data: Any):
        """Set item in cache"""
        self.memory_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Trim cache if it's too large
        if len(self.memory_cache) > MAX_CACHE_ITEMS:
            # Remove oldest items
            items = sorted(self.memory_cache.items(), key=lambda x: x[1]['timestamp'])
            self.memory_cache = dict(items[-MAX_CACHE_ITEMS:])
            
        # Save cache to disk
        self._save_cache()

class SpotifyClient:
    """Enhanced client for interacting with the Spotify API""" 
    def __init__(self): 
        self.cache = SpotifyCache()
        try:
            # Log the credentials we're using (without showing full secret)
            client_id = SPOTIFY_CLIENT_ID
            client_secret = SPOTIFY_CLIENT_SECRET
            
            if not client_id or not client_secret:
                logging.error("Spotify credentials are missing. Make sure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are set in .env")
                self.initialized = False
                return
                
            # Log partial credentials for debugging
            logging.info(f"Initializing Spotify client with ID: {client_id[:5]}...{client_id[-5:]} and Secret: {client_secret[:3]}...{client_secret[-3:]}")
            
            self.client_credentials_manager = SpotifyClientCredentials( 
                client_id=client_id,  
                client_secret=client_secret 
            ) 
            self.spotify = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager) 
            
            # Test the connection
            self.spotify.search(q='test', limit=1)
            
            self.initialized = True
            logging.info("Spotify client successfully initialized")
        except Exception as e: 
            logging.error(f"Failed to initialize Spotify client: {e}") 
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

    async def get_track(self, url):
        """Get information about a Spotify track with enhanced metadata"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")
            
        # Check cache first
        cache_key = f"track:{url}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
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
            logging.error(f"Error processing Spotify track URL {url}: {e}")
            # Create a fallback search query using the URL itself
            return {
                'title': f"Spotify Track",
                'artist': "Unknown Artist",
                'album': "Unknown Album",
                'search_query': f"spotify track {url.split('/')[-1].split('?')[0]} audio",
                'album_art': None
            }

    async def get_playlist_tracks(self, url, limit=50, offset=0):
        """Get tracks from a Spotify playlist with pagination support"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")
            
        # Check cache first
        cache_key = f"playlist:{url}:{limit}:{offset}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
        try:
            content_type, playlist_id = self._extract_id_from_url(url)
            if content_type != "playlist":
                raise ValueError(f"URL is not a Spotify playlist: {url}")
                
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
        except Exception as e:
            logging.error(f"Error processing Spotify playlist URL {url}: {e}")
            # Create a fallback result
            return {
                'playlist_name': "Unknown Playlist",
                'playlist_owner': "Unknown",
                'tracks': [{
                    'title': "Spotify Playlist",
                    'artist': "Unknown",
                    'search_query': f"spotify playlist {url.split('/')[-1].split('?')[0]} music audio",
                    'album_art': None
                }],
                'total_tracks': 1,
                'current_offset': 0,
                'limit': limit
            }

    async def get_album_tracks(self, url, limit=50, offset=0):
        """Get tracks from a Spotify album with pagination support"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")
            
        # Check cache first
        cache_key = f"album:{url}:{limit}:{offset}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
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
            logging.error(f"Error processing Spotify album URL {url}: {e}")
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

    async def get_recommendations(self, track_url=None, artist_ids=None, genre_seeds=None, limit=5):
        """Get track recommendations based on a track, artists, or genres"""
        if not self.initialized:
            raise Exception("Spotify client not initialized")
            
        # Check cache first
        cache_key = f"recommendations:{track_url}:{artist_ids}:{genre_seeds}:{limit}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
            
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
            logging.error(f"Error getting Spotify recommendations: {e}")
            return {
                'tracks': [],
                'seed_tracks': [],
                'seed_artists': [],
                'seed_genres': []
            }

    async def parse_spotify_url(self, url):
        """Parse a Spotify URL and return appropriate data"""
        try:
            if not self.initialized:
                logging.error("Cannot parse Spotify URL: Spotify client not initialized")
                raise Exception("Spotify client not initialized. Check your credentials.")
                
            logging.info(f"Parsing Spotify URL: {url}")
            
            if "track" in url:
                logging.info("Detected Spotify track URL")
                return await self.get_track(url)
            elif "playlist" in url:
                logging.info("Detected Spotify playlist URL")
                playlist_data = await self.get_playlist_tracks(url)
                return playlist_data['tracks']
            elif "album" in url:
                logging.info("Detected Spotify album URL")
                album_data = await self.get_album_tracks(url)
                return album_data['tracks']
            else:
                logging.error(f"Unsupported Spotify URL type: {url}")
                raise ValueError(f"Unsupported Spotify URL type: {url}")
        except Exception as e:
            logging.error(f"Error parsing Spotify URL {url}: {e}")
            raise Exception(f"Error processing Spotify URL: {str(e)}")
