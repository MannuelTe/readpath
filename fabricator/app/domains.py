"""Allocate domains from the configured pool, then optionally purchase within budget.

Purchasing requires ``ALLOW_PURCHASE=true``. Registrar adapters implement
``check(domain) -> (available, price)`` and ``buy(domain) -> bool``.
"""
import time
from . import config, db

class DryRunRegistrar:
    def check(self, domain): return True, 12.0
    def buy(self, domain): print(f"[dry run] Would buy {domain}"); return True

REGISTRARS = {"dryrun": DryRunRegistrar}  # Add an adapter here after selecting a registrar.

def seed_pool():
    with db.conn() as c:
        for d in config.DOMAIN_POOL:
            c.execute("INSERT OR IGNORE INTO pages(domain,origin,status,updated_at) VALUES(?,?,?,?)",
                      (d, "pool", "free", time.time()))

def _spent():
    with db.conn() as c:
        return c.execute("SELECT COALESCE(SUM(cost_usd),0) FROM pages").fetchone()[0]

def claim(bait_id: int, suggested: str | None = None):
    """Return the allocated domain, or ``None`` when no domain is available."""
    with db.conn() as c:
        row = c.execute("SELECT domain FROM pages WHERE status='free' LIMIT 1").fetchone()
        if row:
            c.execute("UPDATE pages SET status='claimed', bait_id=?, updated_at=? WHERE domain=?",
                      (bait_id, time.time(), row[0]))
            return row[0]
    if not (config.ALLOW_PURCHASE and suggested):
        return None
    reg = REGISTRARS[config.REGISTRAR]()
    ok, price = reg.check(suggested)
    if not ok or _spent() + price > config.PURCHASE_BUDGET_USD or not reg.buy(suggested):
        return None
    with db.conn() as c:
        c.execute("INSERT OR REPLACE INTO pages(domain,origin,status,bait_id,cost_usd,updated_at) VALUES(?,?,?,?,?,?)",
                  (suggested, "bought", "claimed", bait_id, price, time.time()))
    return suggested
