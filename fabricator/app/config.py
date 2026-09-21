import os

def _f(k, d): return float(os.getenv(k, d))

DB_PATH = os.getenv("DB_PATH", "data/mcp.db")
LATENCY_TARGET_MS = _f("LATENCY_TARGET_MS", 140)
LATENCY_JITTER_MS = _f("LATENCY_JITTER_MS", 50)
ADMIN_TOKEN = os.getenv("MCP_ADMIN_TOKEN", "")
JEV_URL = os.getenv("JEV_URL", "")
JEV_API_KEY = os.getenv("JEV_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
DOMAIN_POOL = [d.strip() for d in os.getenv("DOMAIN_POOL", "").split(",") if d.strip()]
REGISTRAR = os.getenv("REGISTRAR", "dryrun")
ALLOW_PURCHASE = os.getenv("ALLOW_PURCHASE", "false").lower() == "true"
PURCHASE_BUDGET_USD = _f("PURCHASE_BUDGET_USD", 50)
NEXT_STEP_THRESHOLD = _f("NEXT_STEP_THRESHOLD", 0.25)
