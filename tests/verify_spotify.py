# Spotify Integration Verification Script
# This script verifies that all the components needed for Spotify integration
# in the Discord bot are working correctly.

import asyncio
import logging
import os
import re
import requests
from dotenv import load_dotenv
from bot.music.spotify import SpotifyClient
from bot.utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('spotify_verification')

# Load environment variables
load_dotenv()

async def verify_spotify_setup():
    """Verify that Spotify integration is set up correctly"""
    print("\n===== SPOTIFY INTEGRATION VERIFICATION =====")
    
    # Check environment variables
    print("\n[1/5] Checking environment variables...")
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    
    if not client_id:
        print("❌ SPOTIFY_CLIENT_ID is missing or empty")
        return False
    else:
        print(f"✅ SPOTIFY_CLIENT_ID is set: {client_id[:5]}...{client_id[-5:]}")
    
    if not client_secret:
        print("❌ SPOTIFY_CLIENT_SECRET is missing or empty")
        return False
    else:
        print(f"✅ SPOTIFY_CLIENT_SECRET is set: {client_secret[:3]}...{client_secret[-3:]}")
    
    # Verify Spotify client initialization
    print("\n[2/5] Testing Spotify client initialization...")
    spotify_client = SpotifyClient()
    
    if not spotify_client.initialized:
        print("❌ SpotifyClient failed to initialize")
        return False
    else:
        print("✅ SpotifyClient initialized successfully")
    
    # Test URL regex pattern
    print("\n[3/5] Testing URL pattern matching...")
    test_urls = [
        ("https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT", True, "track"),
        ("https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq", True, "playlist"),
        ("https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h", True, "album"),
        ("https://open.spotify.com/invalid/12345", False, None),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", False, None)
    ]
    
    pattern = r'https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'
    
    for url, should_match, url_type in test_urls:
        match = re.match(pattern, url)
        if should_match:
            if match and match.group(1) == url_type:
                print(f"✅ Correctly matched {url_type} URL: {url}")
            else:
                print(f"❌ Failed to match {url_type} URL: {url}")
                return False
        else:
            if not match:
                print(f"✅ Correctly rejected invalid URL: {url}")
            else:
                print(f"❌ Incorrectly matched invalid URL: {url}")
                return False
    
    # Test track URL parsing
    print("\n[4/5] Testing Spotify track URL parsing...")
    track_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
    
    try:
        track_info = await spotify_client.parse_spotify_url(track_url)
        print(f"✅ Successfully parsed track URL")
        print(f"   Title: {track_info['title']}")
        print(f"   Artist: {track_info['artist']}")
        print(f"   Search query: {track_info['search_query'][:50]}...")
    except Exception as e:
        print(f"❌ Failed to parse track URL: {e}")
        return False
    
    # Test playlist URL parsing
    print("\n[5/5] Testing Spotify playlist URL parsing...")
    playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq"
    
    try:
        playlist_tracks = await spotify_client.parse_spotify_url(playlist_url)
        if isinstance(playlist_tracks, list) and len(playlist_tracks) > 0:
            print(f"✅ Successfully parsed playlist URL")
            print(f"   Found {len(playlist_tracks)} tracks")
            print(f"   First track: {playlist_tracks[0]['title']} by {playlist_tracks[0]['artist']}")
        else:
            print(f"❌ Playlist parsing returned invalid result: {playlist_tracks}")
            return False
    except Exception as e:
        print(f"❌ Failed to parse playlist URL: {e}")
        return False
    
    # All tests passed
    print("\n===== VERIFICATION COMPLETE =====")
    print("✅ All Spotify integration tests passed!")
    print("\nYour Discord bot is ready to play music from Spotify!")
    print("Try the following commands:")
    print("  /play https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT")
    print("  /play https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq")
    print("  /play https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h")
    return True

if __name__ == "__main__":
    asyncio.run(verify_spotify_setup())
