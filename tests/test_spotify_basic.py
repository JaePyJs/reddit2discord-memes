import os
import re
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_id_from_url(url):
    """Extract ID from Spotify URL"""
    pattern = r'https?://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)'
    match = re.match(pattern, url)
    
    if not match:
        print(f"Invalid Spotify URL format: {url}")
        return None, None
        
    return match.group(1), match.group(2)  # Return type and ID

def test_basic_spotify():
    """Test basic Spotify functionality without using the full client"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print(f"Testing with credentials:")
    print(f"- Client ID: {client_id[:5]}...{client_id[-5:]}")
    print(f"- Client Secret: {client_secret[:3]}...{client_secret[-3:]}")
    
    # Test URL parsing
    test_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
    content_type, content_id = extract_id_from_url(test_url)
    print(f"\nURL parsing: {test_url}")
    print(f"Content type: {content_type}")
    print(f"Content ID: {content_id}")
    
    # Test basic authentication (just getting the token)
    try:
        auth_url = "https://accounts.spotify.com/api/token"
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        })
        
        if auth_response.status_code == 200:
            print("\n✅ Basic authentication successful!")
            token_data = auth_response.json()
            access_token = token_data['access_token']
            print(f"Got token: {access_token[:10]}...")
            
            # Try a simple API request
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            track_url = f"https://api.spotify.com/v1/tracks/{content_id}"
            
            print(f"\nTesting API request to: {track_url}")
            track_response = requests.get(track_url, headers=headers)
            
            if track_response.status_code == 200:
                track_data = track_response.json()
                print(f"✅ API request successful!")
                print(f"Track name: {track_data['name']}")
                print(f"Artist: {', '.join([artist['name'] for artist in track_data['artists']])}")
            else:
                print(f"❌ API request failed with status code: {track_response.status_code}")
                print(f"Response: {track_response.text[:200]}")
        else:
            print(f"❌ Authentication failed with status code: {auth_response.status_code}")
            print(f"Response: {auth_response.text[:200]}")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    print("Testing Spotify functionality...\n")
    test_basic_spotify()
