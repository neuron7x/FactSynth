from __future__ import annotations

import os
import sqlite3
import time

DB = os.getenv("FEEDBACK_DB", "var/feedback.sqlite3")
os.makedirs(os.path.dirname(DB), exist_ok=True)
conn = sqlite3.connect(DB, check_same_thread=False)
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS feedback(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts INTEGER NOT NULL,
      session_id TEXT,
      request_id TEXT,
      rating INTEGER CHECK(rating BETWEEN 1 AND 5),
      comment TEXT,
      tags TEXT
    );
    """
)
conn.commit()


def insert(session_id: str, request_id: str, rating: int, comment: str = "", tags: str = "") -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO feedback(ts,session_id,request_id,rating,comment,tags) VALUES(?,?,?,?,?,?)",
        (int(time.time()), session_id, request_id, rating, comment, tags),
    )
    conn.commit()
    return cur.lastrowid


def latest(limit: int = 50) -> list[tuple]:
    cur = conn.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (limit,))
    return list(cur)
