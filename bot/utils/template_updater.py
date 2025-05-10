import os
import shutil
import requests
import logging

TEMPLATE_DIR = 'templates'
REMOTE_TEMPLATE_LIST_URL = os.getenv('REMOTE_TEMPLATE_LIST_URL')  # Optional: set in .env
REMOTE_TEMPLATE_BASE_URL = os.getenv('REMOTE_TEMPLATE_BASE_URL')  # Optional: set in .env

# Scan local directory for new templates and copy to TEMPLATE_DIR
def update_local_templates(source_dir):
    if not os.path.exists(source_dir):
        return 0
    count = 0
    for fname in os.listdir(source_dir):
        src = os.path.join(source_dir, fname)
        dst = os.path.join(TEMPLATE_DIR, fname)
        if os.path.isfile(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            count += 1
    return count

# Download templates from a remote list (expects list of filenames)
def update_remote_templates():
    if not REMOTE_TEMPLATE_LIST_URL or not REMOTE_TEMPLATE_BASE_URL:
        return 0
    try:
        resp = requests.get(REMOTE_TEMPLATE_LIST_URL)
        if resp.status_code != 200:
            return 0
        filenames = resp.json() if resp.headers.get('content-type','').startswith('application/json') else resp.text.splitlines()
        count = 0
        for fname in filenames:
            url = f"{REMOTE_TEMPLATE_BASE_URL}/{fname}"
            dst = os.path.join(TEMPLATE_DIR, fname)
            if not os.path.exists(dst):
                r = requests.get(url, stream=True)
                if r.status_code == 200:
                    with open(dst, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    count += 1
        return count
    except Exception as e:
        logging.error(f"Remote template update failed: {e}")
        return 0
