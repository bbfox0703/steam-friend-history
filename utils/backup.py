import os
import shutil
from datetime import datetime

def backup_today():
    src_file = './database/friends.json'
    if not os.path.exists(src_file):
        return

    today = datetime.now().strftime('%Y-%m-%d')
    backup_dir = './backups'
    os.makedirs(backup_dir, exist_ok=True)
    dst_file = os.path.join(backup_dir, f'friends_{today}.json')
    shutil.copyfile(src_file, dst_file)
