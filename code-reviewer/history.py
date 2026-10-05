import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "reviews.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # make SQLite enforce the review_id link
    conn.execute(
        """CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            reviewed_at TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES reviews(id),
            severity TEXT,
            line INTEGER,
            title TEXT,
            category TEXT
        )"""
    )
    return conn


def save_review(filename, issues):
    conn = connect()
    try:
        with conn:  # saves everything together, or nothing if an error happens
            cursor = conn.execute(
                "INSERT INTO reviews (filename, reviewed_at) VALUES (?, ?)",
                (filename, datetime.now().isoformat(timespec="seconds")),
            )
            review_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO issues (review_id, severity, line, title, category) "
                "VALUES (?, ?, ?, ?, ?)",
                [(review_id, i.severity, i.line, i.title, i.category) for i in issues],
            )
    finally:
        conn.close()  # runs even if something above failed


def get_stats():
    conn = connect()
    try:
        total_reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        by_category = conn.execute(
            "SELECT category, COUNT(*) AS n FROM issues GROUP BY category ORDER BY n DESC"
        ).fetchall()
        by_severity = conn.execute(
            "SELECT severity, COUNT(*) AS n FROM issues GROUP BY severity ORDER BY n DESC"
        ).fetchall()
    finally:
        conn.close()
    return total_reviews, by_category, by_severity