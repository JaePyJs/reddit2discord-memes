import sqlite3
import os
from bot.utils.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Templates table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            uploader_id TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_builtin BOOLEAN DEFAULT 0
        )
    ''')

    # User preferences table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            favorite_templates TEXT,
            favorite_style TEXT,
            notify_challenges BOOLEAN DEFAULT 1
        )
    ''')

    # Saved memes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS saved_memes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            meme_url TEXT,
            saved_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Meme history table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meme_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT,
            user_id TEXT,
            meme_url TEXT,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            template_filename TEXT
        )
    ''')

    # Meme ratings table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meme_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meme_id INTEGER,
            user_id TEXT,
            rating INTEGER,
            rated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def add_default_templates():
    """Add default templates to the database"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get all template files
    template_dir = 'templates'
    templates = [f for f in os.listdir(template_dir)
                if os.path.isfile(os.path.join(template_dir, f))
                and f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # Add each template to the database
    for template in templates:
        cur.execute(
            'INSERT OR IGNORE INTO templates (filename, is_builtin) VALUES (?, 1)',
            (template,)
        )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    add_default_templates()
    print('Database initialized with default templates.')
