import os
import subprocess
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

BACKUP_DIR = "backups"


def run_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{BACKUP_DIR}/backup_{timestamp}.sql"
    os.makedirs(BACKUP_DIR, exist_ok=True)

    print(f"Creare backup: {backup_file}...")

    with open(backup_file, "w") as f:
        subprocess.run(["docker", "exec", "financial_dwh_db", "pg_dump", "-U", "dwh_user", "financial_dwh"], stdout=f)

    size = os.path.getsize(backup_file)
    print(f"Backup creat: {backup_file} ({size / 1024:.1f} KB)")
    return backup_file


if __name__ == "__main__":
    run_backup()
