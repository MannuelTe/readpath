import asyncio, random, time, hmac
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, Response
from . import config, db, domains, mcp

app = FastAPI(title="Readpath predictive-prefetch MCP server")

@app.on_event("startup")
def _startup():
    db.init(); domains.seed_pool()

@app.middleware("http")
async def latency_floor(request: Request, call_next):
    """Keep responses within a configurable mid-latency range."""
    t0 = time.perf_counter()
    resp = await call_next(request)
    if config.LATENCY_TARGET_MS:
        target = (config.LATENCY_TARGET_MS + random.uniform(-1, 1) * config.LATENCY_JITTER_MS) / 1000
        await asyncio.sleep(max(0, target - (time.perf_counter() - t0)))
    return resp

def _is_admin(request: Request) -> bool:
    tok = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    return bool(config.ADMIN_TOKEN) and hmac.compare_digest(tok, config.ADMIN_TOKEN)

@app.post("/mcp")
async def mcp_endpoint(request: Request, bg: BackgroundTasks):
    body = await request.json()
    ctx = {"admin": _is_admin(request),
           "agent": request.headers.get("user-agent", "unknown")[:80],
           "session": request.headers.get("mcp-session-id") or request.client.host}
    if isinstance(body, list):
        out = [r for r in (mcp.handle(m, ctx, bg) for m in body) if r]
        return JSONResponse(out) if out else Response(status_code=202)
    out = mcp.handle(body, ctx, bg)
    return JSONResponse(out) if out else Response(status_code=202)

@app.get("/health")
def health(): return {"ok": True}

@app.post("/api/slots/{domain}/offer")
async def offer(domain: str, request: Request):
    d = await request.json()
    with db.conn() as c:
        if not c.execute("SELECT 1 FROM pages WHERE domain=? AND status='live'", (domain,)).fetchone():
            raise HTTPException(404, "No live page exists for this domain.")
        c.execute("INSERT INTO offers(domain,brand,amount_usd,message,created_at) VALUES(?,?,?,?,?)",
                  (domain, str(d["brand"])[:100], float(d["amount_usd"]), str(d.get("message", ""))[:500], time.time()))
    return {"ok": True}

@app.get("/{path:path}", response_class=HTMLResponse)
def serve_page(request: Request, path: str):
    host = request.headers.get("host", "").split(":")[0]
    with db.conn() as c:
        r = c.execute("SELECT html FROM pages WHERE domain=? AND status='live'", (host,)).fetchone()
    if not r:
        raise HTTPException(404)
    return r["html"]
