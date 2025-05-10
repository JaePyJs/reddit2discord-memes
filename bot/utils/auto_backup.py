import os
import shutil
import datetime
import threading
import time
import logging

BACKUP_DIR = 'backups'
DB_FILE = 'meme_bot.db'  # Change if your DB file is named differently
BACKUP_INTERVAL_SECONDS = 3600  # 1 hour

os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_db():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'{DB_FILE}_{timestamp}.bak')
    try:
        shutil.copy2(DB_FILE, backup_path)
        logging.info(f'Automated backup created: {backup_path}')
        return backup_path
    except Exception as e:
        logging.error(f'Automated backup failed: {e}')
        return None

def backup_loop():
    while True:
        backup_db()
        time.sleep(BACKUP_INTERVAL_SECONDS)

def start_auto_backup():
    t = threading.Thread(target=backup_loop, daemon=True)
    t.start()
