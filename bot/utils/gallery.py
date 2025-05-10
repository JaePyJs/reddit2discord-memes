import json
import os

GALLERY_PATH = 'server_galleries.json'

def load_galleries():
    if not os.path.isfile(GALLERY_PATH):
        return {}
    with open(GALLERY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_galleries(galleries):
    with open(GALLERY_PATH, 'w', encoding='utf-8') as f:
        json.dump(galleries, f, indent=2)

def add_meme_to_gallery(server_id, meme_url, author_id):
    galleries = load_galleries()
    sid = str(server_id)
    if sid not in galleries:
        galleries[sid] = []
    galleries[sid].append({'url': meme_url, 'author': str(author_id)})
    save_galleries(galleries)

def get_gallery(server_id):
    galleries = load_galleries()
    return galleries.get(str(server_id), [])
