
import os
import sqlite3
from pathlib import Path

# Use a configurable path. Render's filesystem is temporary unless
# a persistent disk is configured.
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "trainee_results.db"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trainee_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trainee TEXT NOT NULL,
                scenario TEXT,
                decision TEXT,
                result TEXT,
                score INTEGER DEFAULT 0,
                response_time REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_result(trainee, scenario, decision, result,
                score, response_time):
    initialize_database()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO trainee_results
            (trainee, scenario, decision, result, score, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(trainee),
            str(scenario),
            str(decision),
            str(result),
            int(score),
            float(response_time)
        ))


def get_all_results():
    initialize_database()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM trainee_results
            ORDER BY created_at DESC
        """).fetchall()

        return [dict(row) for row in rows]
