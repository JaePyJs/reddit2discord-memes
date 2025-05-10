import json
import json
import os

PROFILE_PATH = 'user_profiles.json'

def load_profiles():
    if not os.path.isfile(PROFILE_PATH):
        return {}
    with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_profiles(profiles):
    with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2)

def get_user_profile(user_id):
    profiles = load_profiles()
    return profiles.get(str(user_id), {'favorites': [], 'styles': []})

def add_favorite_template(user_id, template):
    profiles = load_profiles()
    uid = str(user_id)
    if uid not in profiles:
        profiles[uid] = {'favorites': [], 'styles': []}
    if template not in profiles[uid]['favorites']:
        profiles[uid]['favorites'].append(template)
    save_profiles(profiles)

def add_favorite_style(user_id, style):
    profiles = load_profiles()
    uid = str(user_id)
    if uid not in profiles:
        profiles[uid] = {'favorites': [], 'styles': []}
    if style not in profiles[uid]['styles']:
        profiles[uid]['styles'].append(style)
    save_profiles(profiles)
