import sqlite3
import os

def get_leaderboard(server_id, by='count', limit=10):
    # by: 'count' (memes created), 'rating' (average meme rating)
    db_path = 'meme_history.db'
    if not os.path.isfile(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if by == 'count':
        cur.execute('''
            SELECT user_id, COUNT(*) as memes
            FROM meme_history
            WHERE server_id = ?
            GROUP BY user_id
            ORDER BY memes DESC
            LIMIT ?
        ''', (str(server_id), limit))
        rows = cur.fetchall()
        conn.close()
        return [{'user_id': row[0], 'memes': row[1]} for row in rows]
    elif by == 'rating':
        cur.execute('''
            SELECT user_id, AVG(rating) as avg_rating
            FROM meme_ratings
            WHERE server_id = ?
            GROUP BY user_id
            ORDER BY avg_rating DESC
            LIMIT ?
        ''', (str(server_id), limit))
        rows = cur.fetchall()
        conn.close()
        return [{'user_id': row[0], 'avg_rating': round(row[1],2)} for row in rows]
    else:
        conn.close()
        return []
