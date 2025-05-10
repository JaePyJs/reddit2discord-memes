import json
import os
from datetime import datetime
import random

MOTD_PATH = 'motd.json'

# Save the selected meme of the day for each server and date
def load_motd():
    if not os.path.isfile(MOTD_PATH):
        return {}
    with open(MOTD_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_motd(motds):
    with open(MOTD_PATH, 'w', encoding='utf-8') as f:
        json.dump(motds, f, indent=2)

def pick_meme_of_the_day(server_id, gallery):
    if not gallery:
        return None
    return random.choice(gallery)

def get_motd(server_id):
    motds = load_motd()
    key = f"{server_id}:{datetime.now().date()}"
    return motds.get(key)

def set_motd(server_id, meme):
    motds = load_motd()
    key = f"{server_id}:{datetime.now().date()}"
    motds[key] = meme
    save_motd(motds)
