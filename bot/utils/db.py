import sqlite3

DB_PATH = 'meme_bot.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Meme history table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meme_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            command TEXT,
            meme_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Favorite memes table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS favorite_memes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            meme_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('Database initialized.')
