import sqlite3
import os
import logging
from bot.core.config import DB_PATH

def init_db():
    """Initialize the database"""
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        creator_id TEXT,
        creator_name TEXT,
        width INTEGER,
        height INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS memes (
        id INTEGER PRIMARY KEY,
        template_id INTEGER,
        creator_id TEXT,
        creator_name TEXT,
        file_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES templates (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS spotify_cache (
        id INTEGER PRIMARY KEY,
        url TEXT NOT NULL,
        data TEXT NOT NULL,
        timestamp INTEGER NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    logging.info("Database initialized")

def add_default_templates():
    """Add default templates to the database if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if templates table is empty
    c.execute("SELECT COUNT(*) FROM templates")
    count = c.fetchone()[0]
    
    if count == 0:
        # Add default templates
        templates = [
            ("drake", "templates/drake.jpg", "SYSTEM", "System", 717, 717),
            ("distracted_boyfriend", "templates/distracted_boyfriend.jpg", "SYSTEM", "System", 1200, 800),
            ("change_my_mind", "templates/change_my_mind.jpg", "SYSTEM", "System", 924, 583),
            ("two_buttons", "templates/two_buttons.jpg", "SYSTEM", "System", 600, 908),
            ("expanding_brain", "templates/expanding_brain.jpg", "SYSTEM", "System", 857, 1202),
            ("surprised_pikachu", "templates/surprised_pikachu.jpg", "SYSTEM", "System", 1893, 1893),
            ("this_is_fine", "templates/this_is_fine.jpg", "SYSTEM", "System", 580, 282),
            ("stonks", "templates/stonks.jpg", "SYSTEM", "System", 442, 331)
        ]
        
        c.executemany(
            "INSERT INTO templates (name, file_path, creator_id, creator_name, width, height) VALUES (?, ?, ?, ?, ?, ?)",
            templates
        )
        
        conn.commit()
        logging.info(f"Added {len(templates)} default templates")
    
    conn.close()

def get_spotify_cache(url):
    """Get cached Spotify data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT data, timestamp FROM spotify_cache WHERE url = ?", (url,))
    result = c.fetchone()
    
    conn.close()
    
    return result

def set_spotify_cache(url, data, timestamp):
    """Set cached Spotify data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if entry exists
    c.execute("SELECT id FROM spotify_cache WHERE url = ?", (url,))
    result = c.fetchone()
    
    if result:
        # Update existing entry
        c.execute("UPDATE spotify_cache SET data = ?, timestamp = ? WHERE url = ?", (data, timestamp, url))
    else:
        # Insert new entry
        c.execute("INSERT INTO spotify_cache (url, data, timestamp) VALUES (?, ?, ?)", (url, data, timestamp))
    
    conn.commit()
    conn.close()

def clear_old_spotify_cache(max_age):
    """Clear old Spotify cache entries"""
    import time
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    current_time = int(time.time())
    cutoff_time = current_time - max_age
    
    c.execute("DELETE FROM spotify_cache WHERE timestamp < ?", (cutoff_time,))
    deleted_count = c.rowcount
    
    conn.commit()
    conn.close()
    
    logging.info(f"Cleared {deleted_count} old Spotify cache entries")
