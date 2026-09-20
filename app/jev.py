"""Next-step prediction.

Jev (TypeSafe AI) is a "System 1" model: you define the possible outputs and it returns
probabilities. Its request schema is not publicly documented, so `_call_jev` is the single
place to adapt once you have docs.typesafe.ai access. Without JEV_URL, or on any failure,
we fall back to an empirical transition table built from logged sessions (scripts/decompose.py
builds the same table offline).
"""
import httpx
from . import config, db

STEPS = ["read_skill", "get_contact_info", "get_pricing", "get_reviews", "get_availability"]

def _table_prediction(last_tool: str):
    with db.conn() as c:
        rows = c.execute(
            """SELECT b.tool AS nxt, COUNT(*) n FROM events a JOIN events b
               ON a.session=b.session AND b.id=(SELECT MIN(id) FROM events
                   WHERE session=a.session AND id>a.id AND tool IS NOT NULL)
               WHERE a.tool=? GROUP BY b.tool""", (last_tool,)).fetchall()
    total = sum(r["n"] for r in rows)
    if not total:  # cold start prior
        return {"read_skill": 0.9, "get_contact_info": 0.5, "get_pricing": 0.4}
    return {r["nxt"]: r["n"] / total for r in rows}

def _call_jev(context: dict) -> dict:
    # ADAPT: request/response shape is a placeholder until the real schema is available.
    r = httpx.post(config.JEV_URL, timeout=2.0,
                   headers={"Authorization": f"Bearer {config.JEV_API_KEY}"},
                   json={"input": context, "outputs": {"next_step": STEPS}})
    r.raise_for_status()
    return r.json()["probabilities"]

def predict_next(last_tool: str, bait_line: str) -> list[tuple[str, float]]:
    probs = None
    if config.JEV_URL:
        try:
            probs = _call_jev({"last_tool": last_tool, "query": bait_line})
        except Exception:
            probs = None
    probs = probs or _table_prediction(last_tool)
    ranked = sorted(probs.items(), key=lambda kv: -kv[1])
    return [(s, p) for s, p in ranked if p >= config.NEXT_STEP_THRESHOLD]
