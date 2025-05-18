import json
import os
from datetime import datetime, timedelta
import random

CHALLENGES_PATH = 'meme_challenges.json'

THEMES = [
    'Animals', 'Politics', 'Gaming', 'Wholesome', 'Dank',
    'Relatable', 'Classic', 'Seasonal', 'Technology', 'Food', 'Movies', 'Music'
]

def load_challenges():
    if not os.path.isfile(CHALLENGES_PATH):
        return {}
    with open(CHALLENGES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_challenges(challenges):
    with open(CHALLENGES_PATH, 'w', encoding='utf-8') as f:
        json.dump(challenges, f, indent=2)

def start_challenge(server_id, theme=None, duration_hours=24):
    challenges = load_challenges()
    sid = str(server_id)
    if not theme:
        theme = random.choice(THEMES)
    end_time = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
    challenges[sid] = {
        'theme': theme,
        'end_time': end_time,
        'entries': []
    }
    save_challenges(challenges)
    return theme, end_time

def add_entry(server_id, user_id, meme_url):
    challenges = load_challenges()
    sid = str(server_id)
    if sid not in challenges:
        return False
    challenges[sid]['entries'].append({'user': str(user_id), 'url': meme_url})
    save_challenges(challenges)
    return True

def get_challenge(server_id):
    challenges = load_challenges()
    return challenges.get(str(server_id))

def end_challenge(server_id):
    challenges = load_challenges()
    sid = str(server_id)
    if sid in challenges:
        del challenges[sid]
        save_challenges(challenges)
