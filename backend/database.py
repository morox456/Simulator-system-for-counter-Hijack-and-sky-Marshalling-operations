
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "trainee_results.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
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
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO trainee_results
            (trainee, scenario, decision, result, score, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            trainee, scenario, decision, result,
            score, response_time
        ))


def get_all_results():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM trainee_results
            ORDER BY created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]
