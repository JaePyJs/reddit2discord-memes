import json
import os
from typing import Dict, Any

STORE_PATH = 'autopost_store.json'

_DEFAULT_CFG: Dict[str, Any] = {
    'channel_id': None,
    'last_posted_id': None,
    'last_post_ts': 0,
    'seen_ids': []
}


def load_store():
    if not os.path.isfile(STORE_PATH):
        return {}
    try:
        with open(STORE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_store(store):
    try:
        for guild_id, guild_map in store.items():
            for subreddit, sub_cfg in guild_map.items():
                if len(sub_cfg['seen_ids']) > 500:
                    sub_cfg['seen_ids'] = sub_cfg['seen_ids'][-500:]
        with open(STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(store, f, indent=2)
    except Exception as e:
        print(f"Failed to save autopost store: {e}")


def _ensure_guild(store, guild_id: int):
    gid = str(guild_id)
    if gid not in store:
        store[gid] = {}
    return store[gid]


def add_subreddit(guild_id: int, subreddit: str, channel_id: int):
    store = load_store()
    guild_map = _ensure_guild(store, guild_id)
    sub_cfg = guild_map.get(subreddit, {})
    if not sub_cfg:
        sub_cfg = _DEFAULT_CFG.copy()
    sub_cfg['channel_id'] = channel_id
    guild_map[subreddit] = sub_cfg
    save_store(store)


def remove_subreddit(guild_id: int, subreddit: str) -> bool:
    store = load_store()
    guild_map = store.get(str(guild_id), {})
    if subreddit in guild_map:
        del guild_map[subreddit]
        save_store(store)
        return True
    return False


def get_subreddits(guild_id: int):
    store = load_store()
    return store.get(str(guild_id), {})
