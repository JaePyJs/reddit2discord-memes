import requests
import random
import logging

# Use a proper User-Agent to comply with Reddit's API guidelines
USER_AGENT = 'RedditDiscordMemeBot/1.0 (by u/JaePyJs)'
REDDIT_URL = 'https://www.reddit.com'
HEADERS = {'User-Agent': USER_AGENT}

POPULAR_MEME_SUBS = [
    'memes', 'dankmemes', 'wholesomememes', 'AdviceAnimals', 'MemeEconomy',
    'me_irl', 'funny', 'PrequelMemes', 'terriblefacebookmemes', 'historymemes'
]

def fetch_top_memes(subreddit=None, limit=5, time_filter='day'):
    if not subreddit:
        subreddit = random.choice(POPULAR_MEME_SUBS)

    # Try different time filters if the first one doesn't work
    time_filters = [time_filter, 'week', 'month', 'all']

    for current_filter in time_filters:
        # Print debug info
        logging.info(f"Fetching from r/{subreddit} with time filter: {current_filter}")

        url = f'{REDDIT_URL}/r/{subreddit}/top.json'
        params = {'limit': 25, 't': current_filter}  # Fetch more posts to increase chances of finding images

        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()

                # Check if we got valid data
                if 'data' in data and 'children' in data['data']:
                    posts = data['data']['children']
                    logging.info(f"Found {len(posts)} posts in r/{subreddit}")

                    # Filter for image posts with more formats
                    memes = []
                    for p in posts:
                        post_data = p.get('data', {})
                        post_url = post_data.get('url', '')

                        # Check for direct image links
                        if post_url.endswith(('.jpg', '.png', '.jpeg', '.gif', '.webp')):
                            memes.append(post_url)
                        # Check for Reddit gallery
                        elif 'gallery' in post_url or post_data.get('is_gallery', False):
                            # For galleries, we can only get the thumbnail
                            if 'thumbnail' in post_data and post_data['thumbnail'].startswith('http'):
                                memes.append(post_data['thumbnail'])

                    logging.info(f"Found {len(memes)} meme images in r/{subreddit}")

                    # If we found enough memes, return them
                    if len(memes) >= limit:
                        return memes[:limit]
                else:
                    logging.warning(f"Invalid data structure from Reddit for r/{subreddit}")
            else:
                logging.warning(f"Reddit returned status code {resp.status_code} for r/{subreddit}")

        except Exception as e:
            logging.error(f"Error fetching from Reddit: {e}")

    # If we get here, we couldn't find enough memes with any time filter
    return []


def fetch_newest_meme(subreddit):
    """Fetch the newest meme from a subreddit with title, author, and image URL."""
    logging.info(f"Fetching newest meme from r/{subreddit}")

    url = f'{REDDIT_URL}/r/{subreddit}/new.json'
    params = {'limit': 25}  # Fetch several posts to find an image

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)

        if resp.status_code == 200:
            data = resp.json()

            if 'data' in data and 'children' in data['data']:
                posts = data['data']['children']
                logging.info(f"Found {len(posts)} new posts in r/{subreddit}")

                # Look for image posts
                for p in posts:
                    post_data = p.get('data', {})
                    post_url = post_data.get('url', '')
                    post_title = post_data.get('title', 'No Title')
                    post_author = post_data.get('author', 'Unknown')
                    post_permalink = post_data.get('permalink', '')

                    # Check for direct image links
                    is_image = post_url.endswith(('.jpg', '.png', '.jpeg', '.gif', '.webp'))
                    is_gallery = 'gallery' in post_url or post_data.get('is_gallery', False)

                    if is_image or is_gallery:
                        # For galleries, use the thumbnail if available
                        if is_gallery and 'thumbnail' in post_data and post_data['thumbnail'].startswith('http'):
                            post_url = post_data['thumbnail']

                        # Create full Reddit post URL
                        reddit_post_url = f"{REDDIT_URL}{post_permalink}"

                        # Include the post ID for tracking
                        post_id = post_data.get('id', '')
                        return {
                            'id': post_id,  # Add post ID for tracking
                            'title': post_title,
                            'author': post_author,
                            'image_url': post_url,
                            'post_url': reddit_post_url
                        }

                logging.warning(f"No image posts found in r/{subreddit}")
            else:
                logging.warning(f"Invalid data structure from Reddit for r/{subreddit}")
        else:
            logging.warning(f"Reddit returned status code {resp.status_code} for r/{subreddit}")

    except Exception as e:
        logging.error(f"Error fetching from Reddit: {e}")

    return None

def fetch_random_new_meme(subreddit, exclude_ids=None, limit=25):
    """Fetch a random image meme from subreddit new posts, excluding any IDs in exclude_ids."""
    if exclude_ids is None:
        exclude_ids = set()
    url = f'{REDDIT_URL}/r/{subreddit}/new.json'
    params = {'limit': limit}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            logging.warning(f"Reddit status {resp.status_code} for r/{subreddit}")
            return None
        data = resp.json()
        posts = data.get('data', {}).get('children', [])
        candidates = []
        for p in posts:
            d = p.get('data', {})
            pid = d.get('id')
            if not pid or pid in exclude_ids:
                continue
            url_ = d.get('url', '')
            is_img = url_.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
            is_gallery = 'gallery' in url_ or d.get('is_gallery', False)
            if not (is_img or is_gallery):
                continue
            if is_gallery and d.get('thumbnail', '').startswith('http'):
                url_ = d['thumbnail']
            candidates.append({
                'id': pid,
                'title': d.get('title', 'No Title'),
                'author': d.get('author', 'Unknown'),
                'image_url': url_,
                'post_url': f"{REDDIT_URL}{d.get('permalink', '')}"
            })
        if not candidates:
            logging.warning(f"No new image memes found in r/{subreddit}")
            return None
        return random.choice(candidates)
    except Exception as e:
        logging.error(f"Random meme fetch error: {e}")
        return None

def fetch_new_posts(subreddit, limit=10):
    """Return list of newest image posts sorted newest->older."""
    url = f"{REDDIT_URL}/r/{subreddit}/new.json"
    params = {'limit': limit}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json().get('data', {}).get('children', [])
        results = []
        for p in data:
            d = p.get('data', {})
            post_url = d.get('url', '')
            is_img = post_url.endswith(('.jpg', '.png', '.jpeg', '.gif', '.webp'))
            is_gallery = 'gallery' in post_url or d.get('is_gallery', False)
            is_video = d.get('is_video', False)
            is_text = bool(d.get('selftext'))

            if not (is_img or is_gallery or is_video or is_text):
                continue
                
            # For galleries, use thumbnail
            if is_gallery and d.get('thumbnail', '').startswith('http'):
                post_url = d['thumbnail']
                
            results.append({
                'id': d.get('id', ''),
                'title': d.get('title', 'No Title'),
                'author': d.get('author', 'Unknown'),
                'image_url': post_url if is_img or is_gallery else None,
                'video_url': d.get('media', {}).get('reddit_video', {}).get('fallback_url') if is_video else None,
                'text': d.get('selftext') if is_text else None,
                'post_url': f"{REDDIT_URL}{d.get('permalink', '')}",
                'created_utc': d.get('created_utc', 0),
                'score': d.get('score', 0),
                'num_comments': d.get('num_comments', 0)
            })
        return results
    except Exception as e:
        logging.error(f"Error fetching new posts: {e}")
        return []

def fetch_random_best_post(subreddit, limit=100):
    """Return a random image post from best sort (top all-time) with image."""
    url = f"{REDDIT_URL}/r/{subreddit}/best.json"
    params = {'limit': limit}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        children = r.json().get('data', {}).get('children', [])
        candidates = []
        for p in children:
            d = p['data']
            u = d.get('url', '')
            is_img = u.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
            is_gallery = 'gallery' in u or d.get('is_gallery', False)
            
            if not (is_img or is_gallery):
                continue
                
            # For galleries, use thumbnail
            if is_gallery and d.get('thumbnail', '').startswith('http'):
                u = d['thumbnail']
                
            candidates.append({
                'id': d.get('id', ''),
                'title': d.get('title', 'No Title'),
                'author': d.get('author', 'Unknown'),
                'image_url': u,
                'post_url': f"{REDDIT_URL}{d.get('permalink', '')}",
                'score': d.get('score', 0),
                'num_comments': d.get('num_comments', 0)
            })
        if not candidates:
            return None
        return random.choice(candidates)
    except Exception as e:
        logging.error(f"Error fetching best post: {e}")
        return None
