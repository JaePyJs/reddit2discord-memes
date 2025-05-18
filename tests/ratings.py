import json
import os

RATINGS_PATH = 'meme_ratings.json'

def load_ratings():
    if not os.path.isfile(RATINGS_PATH):
        return {}
    with open(RATINGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_ratings(ratings):
    with open(RATINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, indent=2)

def rate_meme(meme_id, user_id, rating):
    ratings = load_ratings()
    meme_id = str(meme_id)
    user_id = str(user_id)
    if meme_id not in ratings:
        ratings[meme_id] = {}
    ratings[meme_id][user_id] = rating
    save_ratings(ratings)

def get_meme_rating(meme_id):
    ratings = load_ratings()
    meme_id = str(meme_id)
    if meme_id not in ratings or not ratings[meme_id]:
        return 0, 0  # avg, count
    values = list(ratings[meme_id].values())
    avg = sum(values) / len(values)
    return round(avg, 2), len(values)
