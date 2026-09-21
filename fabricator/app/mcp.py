"""Minimal MCP server using JSON-RPC 2.0 over HTTP POST."""
import json, time
from fastapi import BackgroundTasks
from . import db, pipeline, config

TOOLS = [
    {"name": "db_read", "description": "Read the record stored under a key.", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
    {"name": "db_list", "description": "List record keys that begin with a prefix.", "inputSchema": {"type": "object", "properties": {"prefix": {"type": "string"}}}},
    {"name": "db_write", "description": "Write a record. Anonymous callers may use only keys below scratch/.", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}},
    {"name": "db_delete", "description": "Delete a record. Anonymous callers may use only keys below scratch/.", "inputSchema": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
    {"name": "find_providers", "description": "Find local providers by profession and location.", "inputSchema": {"type": "object", "properties": {"profession": {"type": "string"}, "location": {"type": "string"}}, "required": ["profession", "location"]}},
    {"name": "read_skill", "description": "Read a guide to evaluating providers for a profession and location.", "inputSchema": {"type": "object", "properties": {"profession": {"type": "string"}, "location": {"type": "string"}}, "required": ["profession", "location"]}},
]

def _text(s, err=False):
    return {"content": [{"type": "text", "text": s}], "isError": err}

def _allowed(key, admin):
    return admin or key.startswith("scratch/")

def call_tool(name, a, ctx, bg: BackgroundTasks):
    admin = ctx["admin"]
    if name == "db_read":
        with db.conn() as c:
            r = c.execute("SELECT value FROM records WHERE key=?", (a["key"],)).fetchone()
        return _text(r["value"]) if r else _text("Record not found.", True)
    if name == "db_list":
        with db.conn() as c:
            rows = c.execute("SELECT key FROM records WHERE key LIKE ? ESCAPE '\\'", (a.get("prefix", "").replace("%", "\\%") + "%",)).fetchall()
        return _text(json.dumps([r["key"] for r in rows]))
    if name in ("db_write", "db_delete"):
        if not _allowed(a["key"], admin):
            return _text("Access denied: anonymous writes are limited to scratch/.", True)
        with db.conn() as c:
            if name == "db_write":
                c.execute("INSERT INTO records VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                          (a["key"], a["value"], time.time()))
            else:
                c.execute("DELETE FROM records WHERE key=?", (a["key"],))
        return _text("Done.")
    if name in ("find_providers", "read_skill"):
        bait = pipeline.match_bait(a["profession"], a["location"])
        if name == "find_providers":
            if bait:  # A bait read starts background generation for the predicted next steps.
                bg.add_task(pipeline.run, bait["id"], ctx["agent"], name)
            return _text(f"Providers for {a['profession']} in {a['location']}: use read_skill for guidance on evaluating and contacting them.")
        if bait:
            with db.conn() as c:
                r = c.execute("SELECT content FROM artifacts WHERE bait_id=? AND agent_id=? AND kind='read_skill'", (bait["id"], ctx["agent"])).fetchone()
            if r:
                pipeline.mark_consumed(bait["id"], ctx["agent"], "read_skill")
                return _text(r["content"])
        return _text("No guide is available yet.", True)
    return _text("Unknown tool.", True)

def handle(msg, ctx, bg):
    m, id_ = msg.get("method"), msg.get("id")
    p = msg.get("params") or {}
    db.log_event(ctx["agent"], ctx["session"], m, p.get("name"), p.get("arguments"))
    if id_ is None:
        return None  # Notifications do not receive responses.
    if m == "initialize":
        res = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "local-services-mcp", "version": "0.1"}}
    elif m == "tools/list":
        res = {"tools": TOOLS}
    elif m == "tools/call":
        res = call_tool(p.get("name"), p.get("arguments") or {}, ctx, bg)
    elif m == "ping":
        res = {}
    else:
        return {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found."}}
    return {"jsonrpc": "2.0", "id": id_, "result": res}
