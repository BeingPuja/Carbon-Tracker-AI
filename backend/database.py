import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "carbon_tracker.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        distance REAL,
        mode TEXT,
        kwh REAL,
        meals REAL,
        diet TEXT,
        transport_em REAL,
        energy_em REAL,
        diet_em REAL,
        total REAL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        UNIQUE(user_id, date)
    )
    """)


    conn.commit()
    conn.close()


# Initialize database automatically
init_db()
