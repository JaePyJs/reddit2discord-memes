import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to see detailed information
logging.basicConfig(level=logging.INFO)

# Spotify API credentials from environment variables
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

def test_spotify_auth():
    """Test the Spotify authentication with the provided credentials."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ ERROR: Spotify credentials not found in .env file")
        print("Make sure you've added SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file")
        return
        
    print(f"Testing Spotify authentication with:")
    print(f"- Client ID: {SPOTIFY_CLIENT_ID[:5]}...{SPOTIFY_CLIENT_ID[-5:]}")
    print(f"- Client Secret: {SPOTIFY_CLIENT_SECRET[:3]}...{SPOTIFY_CLIENT_SECRET[-3:]}")
    
    try:
        # Initialize the Spotify client with credentials
        client_credentials_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test a simple API call - just get a new release to verify authentication
        print("\nAttempting to authenticate with Spotify...")
        results = spotify.new_releases(limit=1)
        
        # If we get here, the connection was successful
        print(f"\n✅ SUCCESS! Authenticated with Spotify API successfully")
        print(f"Retrieved latest release: {results['albums']['items'][0]['name']} by {results['albums']['items'][0]['artists'][0]['name']}")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to authenticate with Spotify API")
        print(f"Error details: {str(e)}")
        print("\nPossible reasons for this error:")
        print("1. The client ID and client secret are invalid or expired")
        print("2. The Spotify API is currently experiencing issues")
        print("3. There might be network connectivity problems")

if __name__ == "__main__":
    test_spotify_auth()
