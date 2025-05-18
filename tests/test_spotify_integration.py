import os
import asyncio
import logging
from dotenv import load_dotenv
from bot.music.player import YTDLSource
from bot.music.spotify import SpotifyClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_spotify_integration():
    """Test integrated Spotify functionality as it would be used in the Discord bot"""
    print("\n===== SPOTIFY INTEGRATION TEST =====")
    
    # Initialize Spotify client
    spotify_client = SpotifyClient()
    YTDLSource.spotify_client = spotify_client
    
    if not spotify_client.initialized:
        print("❌ Spotify client failed to initialize")
        return False
    
    print("✅ Spotify client initialized successfully")
    
    # Test a Spotify track URL
    test_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
    print(f"\nTesting integration with track URL: {test_url}")
    
    try:
        # First, get the Spotify track info
        track_info = await spotify_client.parse_spotify_url(test_url)
        print(f"✅ Obtained Spotify track info:")
        print(f"   Title: {track_info['title']}")
        print(f"   Artist: {track_info['artist']}")
        print(f"   Search query: {track_info['search_query']}")
        
        # Next, simulate what happens in the play command
        print("\nSimulating YouTube search and extraction (this might take a moment)...")
        try:
            source = await YTDLSource.create_source(track_info['search_query'])
            print(f"✅ Successfully found matching YouTube content:")
            print(f"   Title: {source.get('title', 'Unknown')}")
            print(f"   Duration: {source.get('duration', 'Unknown')} seconds")
            print(f"   URL: {source.get('webpage_url', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ Error during YouTube search: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error during Spotify integration test: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_spotify_integration())
