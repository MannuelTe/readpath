"""Extract common call sequences from MCP logs and create bait records.

  python -m scripts.decompose baits --professions plumber,electrician --locations zurich,bern
  python -m scripts.decompose flows            # Print next-tool transition probabilities.
"""
import argparse, itertools
from collections import Counter, defaultdict
from app import db

def baits(professions, locations):
    db.init()
    with db.conn() as c:
        for a, b in itertools.product(professions, locations):
            c.execute("INSERT OR IGNORE INTO baits(a,b,line) VALUES(?,?,?)", (a, b, f"{a} in {b}".lower()))
    print(f"{len(professions) * len(locations)} bait records ready")

def flows():
    with db.conn() as c:
        rows = c.execute("SELECT session, tool FROM events WHERE tool IS NOT NULL ORDER BY session, id").fetchall()
    seqs = defaultdict(list)
    for r in rows: seqs[r["session"]].append(r["tool"])
    trans = defaultdict(Counter)
    for s in seqs.values():
        for x, y in zip(s, s[1:]): trans[x][y] += 1
    for x, cnt in trans.items():
        n = sum(cnt.values())
        print(x, "->", {y: round(v / n, 2) for y, v in cnt.most_common()})

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("baits"); b.add_argument("--professions", required=True); b.add_argument("--locations", required=True)
    sp.add_parser("flows")
    a = ap.parse_args()
    if a.cmd == "baits": baits(a.professions.split(","), a.locations.split(","))
    else: flows()
