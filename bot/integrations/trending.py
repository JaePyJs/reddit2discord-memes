import requests

def get_trending_memes(limit=10):
    """
    Fetch trending meme formats from Reddit (e.g., r/MemeTemplatesOfficial hot posts).
    Returns a list of (title, url) tuples.
    """
    url = f'https://www.reddit.com/r/MemeTemplatesOfficial/hot.json?limit={limit}'
    headers = {'User-agent': 'discord-meme-bot/1.0'}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    posts = resp.json()['data']['children']
    results = []
    for p in posts:
        data = p['data']
        if data.get('post_hint') == 'image':
            results.append((data['title'], data['url']))
    return results
