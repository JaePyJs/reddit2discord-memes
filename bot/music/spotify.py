import spotipy 
from spotipy.oauth2 import SpotifyClientCredentials 
import logging 
import re
import requests
from bot.utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET 
 
class SpotifyClient:
    """Client for interacting with the Spotify API""" 
    def __init__(self): 
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

    def _get_title_from_url(self, url):
        """Try to extract title from Spotify URL HTML"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Try to find the title tag in the HTML
                title_match = re.search(r'<title>(.*?)</title>', response.text)
                if title_match:
                    title = title_match.group(1)
                    # Clean up the title (usually in format "Song Name - Artist - Spotify")
                    if " - " in title:
                        parts = title.split(" - ")
                        if len(parts) >= 2:
                            return parts[0], parts[1]  # Return title, artist
            return None, None
        except Exception as e:
            logging.warning(f"Error getting title from URL: {e}")
            return None, None

    async def get_track(self, url):
        """Get information about a Spotify track"""
        try:
            # Extract track ID from URL
            content_type, track_id = self._extract_id_from_url(url)
            if content_type != "track":
                raise ValueError(f"URL is not a Spotify track: {url}")
                
            # Try to get title from URL
            title, artist = self._get_title_from_url(url)
            
            if not title or not artist:
                # If can't get from HTML, use a generic title with the ID
                title = f"Spotify Track {track_id}"
                artist = "Unknown Artist"
                
            # Generate a search query for the player to use
            search_query = f"{title} {artist} audio"
            
            return {
                'title': title,
                'artist': artist,
                'search_query': search_query
            }
        except Exception as e:
            logging.error(f"Error processing Spotify track URL {url}: {e}")
            # Create a fallback search query using the URL itself
            return {
                'title': f"Spotify Track",
                'artist': "Unknown Artist",
                'search_query': f"spotify track {url.split('/')[-1].split('?')[0]} audio"
            }

    async def get_playlist_tracks(self, url):
        """Get tracks from a Spotify playlist"""
        try:
            content_type, playlist_id = self._extract_id_from_url(url)
            if content_type != "playlist":
                raise ValueError(f"URL is not a Spotify playlist: {url}")
                
            # For playlists, we'll create a single dummy track since we can't
            # access the actual tracks without API authentication
            title, owner = self._get_title_from_url(url)
            
            if not title:
                title = f"Spotify Playlist {playlist_id}"
                owner = "Unknown"
                
            logging.info(f"Processing Spotify playlist: {title} by {owner}")
            
            # Return a single dummy track to represent the playlist
            # The music player will search for this track on YouTube
            return [{
                'title': f"{title} Track",
                'artist': owner,
                'search_query': f"music playlist {title} {owner} audio"
            }]
        except Exception as e:
            logging.error(f"Error processing Spotify playlist URL {url}: {e}")
            # Create a fallback result
            return [{
                'title': "Spotify Playlist",
                'artist': "Unknown",
                'search_query': f"spotify playlist {url.split('/')[-1].split('?')[0]} music audio"
            }]

    async def get_album_tracks(self, url):
        """Get tracks from a Spotify album"""
        try:
            content_type, album_id = self._extract_id_from_url(url)
            if content_type != "album":
                raise ValueError(f"URL is not a Spotify album: {url}")
                
            # For albums, we'll create a single dummy track since we can't
            # access the actual tracks without API authentication
            title, artist = self._get_title_from_url(url)
            
            if not title:
                title = f"Spotify Album {album_id}"
                artist = "Unknown Artist"
                
            logging.info(f"Processing Spotify album: {title} by {artist}")
            
            # Return a single dummy track to represent the album
            # The music player will search for this track on YouTube
            return [{
                'title': f"{title} Track",
                'artist': artist,
                'search_query': f"{title} {artist} album audio"
            }]
        except Exception as e:
            logging.error(f"Error processing Spotify album URL {url}: {e}")
            # Create a fallback result
            return [{
                'title': "Spotify Album",
                'artist': "Unknown",
                'search_query': f"spotify album {url.split('/')[-1].split('?')[0]} music audio"
            }]

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
                return await self.get_playlist_tracks(url)
            elif "album" in url:
                logging.info("Detected Spotify album URL")
                return await self.get_album_tracks(url)
            else:
                logging.error(f"Unsupported Spotify URL type: {url}")
                raise ValueError(f"Unsupported Spotify URL type: {url}")
        except Exception as e:
            logging.error(f"Error parsing Spotify URL {url}: {e}")
            raise Exception(f"Error processing Spotify URL: {str(e)}")
