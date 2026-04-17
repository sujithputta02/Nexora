import sqlite3
import datetime
import os

# Resolve DB path relative to the project root (parent of backend/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_PROJECT_ROOT, "logs", "audit_log.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            query TEXT,
            response TEXT,
            context_sources TEXT,
            validation_status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_query(user_id, role, query, response, sources, validation_status):
    """
    Logs every query and its outcome to the secure audit log.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (user_id, role, query, response, context_sources, validation_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, role, query, response, str(sources), validation_status, datetime.datetime.now()))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Audit Log Database initialized.")
else:
    # Ensure DB is initialized when imported
    init_db()
