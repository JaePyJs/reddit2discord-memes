import requests
import os

TENOR_API_KEY = os.getenv('TENOR_API_KEY')  # Set this in your .env file
TENOR_TRENDING_URL = 'https://tenor.googleapis.com/v2/featured'
TENOR_SEARCH_URL = 'https://tenor.googleapis.com/v2/search'

def trending_tenor(limit=5):
    params = {
        'key': TENOR_API_KEY,
        'limit': limit,
        'media_filter': 'minimal',
        'contentfilter': 'medium',
    }
    resp = requests.get(TENOR_TRENDING_URL, params=params)
    if resp.status_code == 200:
        data = resp.json().get('results', [])
        return [item['media_formats']['gif']['url'] for item in data if 'media_formats' in item and 'gif' in item['media_formats']]
    return []

def search_tenor(query, limit=5):
    params = {
        'key': TENOR_API_KEY,
        'q': query,
        'limit': limit,
        'media_filter': 'minimal',
        'contentfilter': 'medium',
    }
    resp = requests.get(TENOR_SEARCH_URL, params=params)
    if resp.status_code == 200:
        data = resp.json().get('results', [])
        return [item['media_formats']['gif']['url'] for item in data if 'media_formats' in item and 'gif' in item['media_formats']]
    return []
