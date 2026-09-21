import time, re
from . import db, jev, generator, domains

def _bait(line: str):
    with db.conn() as c:
        return c.execute("SELECT * FROM baits WHERE line=?", (line.strip().lower(),)).fetchone()

def match_bait(profession: str, location: str):
    return _bait(f"{profession} in {location}")

def run(bait_id: int, agent_id: str, last_tool: str):
    """Triggered when an agent reads a bait line: pre-build predicted next steps, claim a domain."""
    with db.conn() as c:
        bait = c.execute("SELECT * FROM baits WHERE id=?", (bait_id,)).fetchone()
        c.execute("UPDATE baits SET hits=hits+1 WHERE id=?", (bait_id,))
    steps = jev.predict_next(last_tool, bait["line"])
    guide = None
    for kind, prob in steps:
        text = generator.generate(kind, bait["a"], bait["b"])
        guide = guide or (text if kind == "read_skill" else None)
        with db.conn() as c:
            c.execute("INSERT OR IGNORE INTO artifacts(bait_id,agent_id,kind,prob,content,created_at) VALUES(?,?,?,?,?,?)",
                      (bait_id, agent_id, kind, prob, text, time.time()))
    slug = re.sub(r"[^a-z0-9]+", "-", bait["line"]).strip("-")
    domain = domains.claim(bait_id, suggested=f"{slug}.com")
    if domain and guide:
        html = generator.render_page(domain, bait["a"], bait["b"], guide)
        with db.conn() as c:
            c.execute("UPDATE pages SET html=?, updated_at=? WHERE domain=?", (html, time.time(), domain))

def mark_consumed(bait_id: int, agent_id: str, kind: str):
    """Once the agent has pulled the artifact, the page goes live for serving/sale."""
    with db.conn() as c:
        c.execute("UPDATE artifacts SET consumed=1 WHERE bait_id=? AND agent_id=? AND kind=?", (bait_id, agent_id, kind))
        if kind == "read_skill":
            c.execute("UPDATE pages SET status='live' WHERE bait_id=? AND html IS NOT NULL", (bait_id,))
