import sqlite3

def check_templates():
    conn = sqlite3.connect('meme_bot.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM templates')
    templates = cur.fetchall()
    
    print(f"Found {len(templates)} templates:")
    for template in templates:
        print(f"  - {template['filename']} (builtin: {template['is_builtin']})")
    
    conn.close()

if __name__ == '__main__':
    check_templates()
