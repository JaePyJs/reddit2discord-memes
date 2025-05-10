import shutil
import os
import datetime

def backup_db(db_path='meme_bot.db', backup_dir='backups'):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f'Database not found: {db_path}')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'meme_bot_{timestamp}.bak')
    shutil.copy2(db_path, backup_file)
    return backup_file

def restore_db(backup_file, db_path='meme_bot.db'):
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f'Backup file not found: {backup_file}')
    shutil.copy2(backup_file, db_path)
    return db_path
