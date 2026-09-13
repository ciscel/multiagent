"""
Local event store. This is the appliance's memory while it has zero
connectivity. Every sensed event + verdict + action lands here with its
rule citation. Nothing here requires a network call.
"""
import sqlite3
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "appliance.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL,
            state_json TEXT,
            rule_id TEXT,
            category TEXT,
            verdict TEXT,
            citation TEXT,
            action_taken TEXT,
            truck_roll INTEGER DEFAULT 0,
            synced INTEGER DEFAULT 0,
            synced_via TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_event(state: dict, result: dict, action_taken: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO events (ts, state_json, rule_id, category, verdict, citation, action_taken, truck_roll) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (time.time(), json.dumps(state), result["rule_id"], result.get("category", "connectivity"),
         result["verdict"], result["citation"], action_taken, 1 if result.get("truck_roll") else 0)
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return event_id


def get_unsynced():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM events WHERE synced = 0 ORDER BY ts ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_synced(event_ids, via: str):
    if not event_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "UPDATE events SET synced = 1, synced_via = ? WHERE id = ?",
        [(via, eid) for eid in event_ids]
    )
    conn.commit()
    conn.close()


def get_recent(limit=25):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM events ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def queue_depth():
    conn = sqlite3.connect(DB_PATH)
    n = conn.execute("SELECT COUNT(*) FROM events WHERE synced = 0").fetchone()[0]
    conn.close()
    return n
