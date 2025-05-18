import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging to see detailed information
logging.basicConfig(level=logging.DEBUG)

# Spotify API credentials from environment variables
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

def test_spotify_connection():
    """Test the Spotify connection with the provided credentials."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("❌ ERROR: Spotify credentials not found in .env file")
        print("Make sure you've added SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file")
        return
        
    print(f"Testing Spotify connection with:")
    print(f"- Client ID: {SPOTIFY_CLIENT_ID[:5]}...{SPOTIFY_CLIENT_ID[-5:]}")
    print(f"- Client Secret: {SPOTIFY_CLIENT_SECRET[:3]}...{SPOTIFY_CLIENT_SECRET[-3:]}")
    
    try:
        # Initialize the Spotify client with credentials
        client_credentials_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test a simple API call
        print("\nAttempting to fetch a playlist...")
        playlist_id = "37i9dQZF1DXdbRLJPSmnyq"  # The playlist ID from your original URL
        results = spotify.playlist(playlist_id)
        
        # If we get here, the connection was successful
        print(f"\n✅ SUCCESS! Connected to Spotify API successfully")
        print(f"Retrieved playlist: {results['name']} by {results['owner']['display_name']}")
        print(f"Contains {len(results['tracks']['items'])} tracks")
        
        # Print first few tracks as a sample
        print("\nSample tracks:")
        for i, item in enumerate(results['tracks']['items'][:5], 1):
            track = item['track']
            print(f"{i}. {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to connect to Spotify API")
        print(f"Error details: {str(e)}")
        print("\nPossible reasons for this error:")
        print("1. The client ID and client secret are invalid or expired")
        print("2. The Spotify API is currently experiencing issues")
        print("3. There might be network connectivity problems")
        print("\nWhat to try next:")
        print("- Create a new application in the Spotify Developer Dashboard")
        print("- Make sure to copy the new client ID and secret correctly")
        print("- Check if the Spotify API status page reports any issues")

if __name__ == "__main__":
    test_spotify_connection()
