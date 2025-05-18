import requests
import os

GIPHY_API_KEY = os.getenv('GIPHY_API_KEY')  # Set this in your .env file
GIPHY_SEARCH_URL = 'https://api.giphy.com/v1/gifs/search'
GIPHY_TRENDING_URL = 'https://api.giphy.com/v1/gifs/trending'

def search_giphy(query, limit=5):
    params = {
        'api_key': GIPHY_API_KEY,
        'q': query,
        'limit': limit,
        'rating': 'pg-13',
    }
    resp = requests.get(GIPHY_SEARCH_URL, params=params)
    if resp.status_code == 200:
        data = resp.json()['data']
        return [item['images']['original']['url'] for item in data]
    return []

def trending_giphy(limit=5):
    params = {
        'api_key': GIPHY_API_KEY,
        'limit': limit,
        'rating': 'pg-13',
    }
    resp = requests.get(GIPHY_TRENDING_URL, params=params)
    if resp.status_code == 200:
        data = resp.json()['data']
        return [item['images']['original']['url'] for item in data]
    return []
