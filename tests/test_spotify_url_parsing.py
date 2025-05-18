import os
import asyncio
import logging
from dotenv import load_dotenv
from bot.music.spotify import SpotifyClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_spotify_url_parsing():
    """Test parsing different types of Spotify URLs"""
    print("Initializing Spotify client...")
    spotify_client = SpotifyClient()
    
    if not spotify_client.initialized:
        print("❌ ERROR: Spotify client failed to initialize. Check credentials and network.")
        return
    
    print("✅ Spotify client initialized successfully!")
    
    # Test URLs
    test_urls = [
        # Add your test playlist URL
        "https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq?si=ce624203ff2a4014",
        # Add a sample track URL 
        "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=8403424afcd24d72",
        # Add a sample album URL
        "https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h?si=f4d35a1e49854dc1"
    ]
    
    for url in test_urls:
        print(f"\n\nTesting URL: {url}")
        print("URL type:", "playlist" if "playlist" in url else "album" if "album" in url else "track")
        
        try:
            result = await spotify_client.parse_spotify_url(url)
            
            if isinstance(result, list):
                # It's a playlist or album
                print(f"✅ Successfully parsed! Found {len(result)} tracks")
                print("\nFirst 3 tracks:")
                for i, track in enumerate(result[:3], 1):
                    print(f"{i}. {track['title']} by {track['artist']}")
            else:
                # It's a single track
                print(f"✅ Successfully parsed single track:")
                print(f"Title: {result['title']}")
                print(f"Artist: {result['artist']}")
                print(f"Search query: {result['search_query']}")
                
        except Exception as e:
            print(f"❌ Error parsing URL: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_spotify_url_parsing())
