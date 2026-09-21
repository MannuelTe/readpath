import sqlite3, time, json
from contextlib import contextmanager
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS records(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS baits(id INTEGER PRIMARY KEY, a TEXT NOT NULL, b TEXT NOT NULL, line TEXT UNIQUE NOT NULL, hits INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS artifacts(id INTEGER PRIMARY KEY, bait_id INTEGER NOT NULL, agent_id TEXT NOT NULL,
  kind TEXT NOT NULL, prob REAL, content TEXT NOT NULL, consumed INTEGER DEFAULT 0, created_at REAL NOT NULL,
  UNIQUE(bait_id, agent_id, kind));
CREATE TABLE IF NOT EXISTS pages(domain TEXT PRIMARY KEY, origin TEXT NOT NULL, bait_id INTEGER, status TEXT NOT NULL,
  html TEXT, cost_usd REAL DEFAULT 0, updated_at REAL);
CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY, domain TEXT NOT NULL, brand TEXT NOT NULL,
  amount_usd REAL NOT NULL, message TEXT, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts REAL NOT NULL, agent_id TEXT, session TEXT, method TEXT, tool TEXT, args TEXT);
CREATE INDEX IF NOT EXISTS ev_session ON events(session, ts);
"""

@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init():
    with conn() as c:
        c.executescript(SCHEMA)

def log_event(agent_id, session, method, tool=None, args=None):
    with conn() as c:
        c.execute("INSERT INTO events(ts,agent_id,session,method,tool,args) VALUES(?,?,?,?,?,?)",
                  (time.time(), agent_id, session, method, tool, json.dumps(args) if args else None))
