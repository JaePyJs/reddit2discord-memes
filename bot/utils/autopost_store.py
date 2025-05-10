# Switched persistence from JSON to SQLite for durability
import os
import sqlite3
from typing import Dict, Any, List, Tuple

# SQLite database lives alongside codebase
DB_PATH = os.getenv('MEME_BOT_DB', 'meme_bot.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    """Create tables if they don't exist (idempotent)."""
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subreddit_configs (
                guild_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                channel_id INTEGER,
                last_posted_id TEXT,
                last_post_ts INTEGER DEFAULT 0,
                last_best_post_ts INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, subreddit)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_posts (
                guild_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                post_id TEXT NOT NULL,
                PRIMARY KEY (guild_id, subreddit, post_id)
            );
            """
        )
        conn.commit()


_ensure_tables()


# Helper dataclass replacement (dict for simplicity)
_DEFAULT_CFG: Dict[str, Any] = {
    'channel_id': None,
    'last_posted_id': None,
    'last_post_ts': 0,
    'seen_ids': [],
    'last_best_post_ts': 0,
}


def _fetch_seen_ids(cur, guild_id: str, subreddit: str) -> List[str]:
    cur.execute(
        "SELECT post_id FROM seen_posts WHERE guild_id=? AND subreddit=?",
        (guild_id, subreddit),
    )
    return [row[0] for row in cur.fetchall()]


def load_store() -> Dict[str, Dict[str, Any]]:
    """Return the full in-memory representation of the store, keyed by guild id."""
    store: Dict[str, Dict[str, Any]] = {}
    with _get_conn() as conn:
        cur = conn.cursor()
        for row in cur.execute("SELECT * FROM subreddit_configs"):
            gid = row['guild_id']
            sub = row['subreddit']
            cfg = {
                'channel_id': row['channel_id'],
                'last_posted_id': row['last_posted_id'],
                'last_post_ts': row['last_post_ts'],
                'last_best_post_ts': row['last_best_post_ts'],
                'seen_ids': _fetch_seen_ids(cur, gid, sub),
            }
            store.setdefault(gid, {})[sub] = cfg
    return store


def save_store(store: Dict[str, Dict[str, Any]]):
    """Persist the entire in-memory store back to SQLite."""
    try:
        with _get_conn() as conn:
            cur = conn.cursor()
            for guild_id, guild_map in store.items():
                for subreddit, cfg in guild_map.items():
                    # keep `seen_ids` manageable
                    if len(cfg['seen_ids']) > 500:
                        cfg['seen_ids'] = cfg['seen_ids'][-500:]

                    # Upsert config row
                    cur.execute(
                        """
                        INSERT INTO subreddit_configs (
                            guild_id, subreddit, channel_id, last_posted_id,
                            last_post_ts, last_best_post_ts
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(guild_id, subreddit) DO UPDATE SET
                            channel_id=excluded.channel_id,
                            last_posted_id=excluded.last_posted_id,
                            last_post_ts=excluded.last_post_ts,
                            last_best_post_ts=excluded.last_best_post_ts;
                        """,
                        (
                            guild_id,
                            subreddit,
                            cfg.get('channel_id'),
                            cfg.get('last_posted_id'),
                            cfg.get('last_post_ts', 0),
                            cfg.get('last_best_post_ts', 0),
                        ),
                    )

                    # Insert seen post ids
                    for pid in cfg.get('seen_ids', []):
                        cur.execute(
                            "INSERT OR IGNORE INTO seen_posts (guild_id, subreddit, post_id) VALUES (?,?,?)",
                            (guild_id, subreddit, pid),
                        )
            conn.commit()
    except Exception as e:
        print(f"Failed to save autopost store: {e}")


# helper for legacy API
def _ensure_guild(store: Dict[str, Dict[str, Any]], guild_id: int):
    gid = str(guild_id)
    if gid not in store:
        store[gid] = {}
    return store[gid]


def add_subreddit(guild_id: int, subreddit: str, channel_id: int):
    """Add or update a subreddit configuration for a guild."""
    store = load_store()
    guild_map = _ensure_guild(store, guild_id)
    sub_cfg = guild_map.get(subreddit, _DEFAULT_CFG.copy())
    sub_cfg['channel_id'] = channel_id
    guild_map[subreddit] = sub_cfg
    save_store(store)


def remove_subreddit(guild_id: int, subreddit: str) -> bool:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM subreddit_configs WHERE guild_id=? AND subreddit=?", (guild_id, subreddit))
        cur.execute("DELETE FROM seen_posts WHERE guild_id=? AND subreddit=?", (guild_id, subreddit))
        conn.commit()
        return cur.rowcount > 0


def get_subreddits(guild_id: int):
    store = load_store()
    return store.get(str(guild_id), {})


# ---- Additional helper for duplicate checks ----


def is_post_seen(guild_id: int, subreddit: str, post_id: str) -> bool:
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM seen_posts WHERE guild_id=? AND subreddit=? AND post_id=? LIMIT 1",
            (guild_id, subreddit, post_id),
        )
        return cur.fetchone() is not None


def mark_post_seen(guild_id: int, subreddit: str, post_id: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_posts (guild_id, subreddit, post_id) VALUES (?,?,?)",
            (guild_id, subreddit, post_id),
        )
        conn.commit()
