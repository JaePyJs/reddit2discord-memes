import os
import asyncio
import logging
from dotenv import load_dotenv
from bot.music.spotify import SpotifyClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_spotify_parsing():
    """Test parsing different types of Spotify URLs with our fixed code"""
    print("\n===== SPOTIFY URL PARSING TEST =====")
    
    # Initialize the Spotify client
    spotify_client = SpotifyClient()
    
    if not spotify_client.initialized:
        print("❌ Spotify client failed to initialize")
        return False
    
    print("✅ Spotify client initialized successfully")
    
    # Test URLs
    test_urls = [
        ("Track", "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"),
        ("Playlist", "https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq"),
        ("Album", "https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h")
    ]
    
    all_passed = True
    
    for url_type, url in test_urls:
        print(f"\nTesting {url_type} URL: {url}")
        
        try:
            result = await spotify_client.parse_spotify_url(url)
            
            if isinstance(result, list):
                # It's a playlist or album
                print(f"✅ Successfully parsed as {url_type.lower()}")
                print(f"   Found {len(result)} tracks")
                print(f"   First track: {result[0]['title']} by {result[0]['artist']}")
                print(f"   Search query: {result[0]['search_query'][:50]}...")
            else:
                # It's a single track
                print(f"✅ Successfully parsed as {url_type.lower()}")
                print(f"   Title: {result['title']}")
                print(f"   Artist: {result['artist']}")
                print(f"   Search query: {result['search_query'][:50]}...")
                
        except Exception as e:
            print(f"❌ Error parsing {url_type} URL: {str(e)}")
            all_passed = False
    
    print("\n===== TEST RESULTS =====")
    if all_passed:
        print("✅ All Spotify URL tests passed!")
    else:
        print("❌ Some tests failed.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(test_spotify_parsing())
