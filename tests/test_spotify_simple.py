import os
import asyncio
import logging
from dotenv import load_dotenv
from bot.music.spotify import SpotifyClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_spotify_integration():
    """Test Spotify functionality integration"""
    print("\n===== SPOTIFY INTEGRATION TEST =====")
    
    # Initialize Spotify client
    spotify_client = SpotifyClient()
    
    if not spotify_client.initialized:
        print("❌ Spotify client failed to initialize")
        return False
    
    print("✅ Spotify client initialized successfully")
    
    # Test a Spotify track URL
    test_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
    print(f"\nTesting integration with track URL: {test_url}")
    
    try:
        # Get the Spotify track info
        track_info = await spotify_client.parse_spotify_url(test_url)
        print(f"✅ Obtained Spotify track info:")
        print(f"   Title: {track_info['title']}")
        print(f"   Artist: {track_info['artist']}")
        print(f"   Search query: {track_info['search_query']}")
        return True
    except Exception as e:
        print(f"❌ Error during Spotify integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_spotify_integration())
