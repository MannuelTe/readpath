# Readpath non-MCP JIT research harness

This directory implements the V2 web/API transport described in the
[top-level threat model](../README.md). Unlike the predictive-prefetch MCP prototype in
[`fabricator/`](../fabricator/), this server sees a query first and generates its answer during that
same HTTP request. It exposes no MCP endpoint and does not use Jev or predict a next tool call.

The harness is deliberately safe to run locally:

- every response and page is labelled `READPATH RESEARCH SIMULATION`;
- every page sends `X-Robots-Tag: noindex, nofollow` and `X-Readpath-Simulation: true`;
- it does not cloak content, buy domains, invent real contact details, or claim that its generated
  pages are independent sources;
- the offline fallback makes the behavior testable without an LLM.

## How it maps to the V2 model

| V2 property | Implementation |
|---|---|
| Complete coverage | Every nonblank query receives either model output or the offline fallback. |
| Adaptation | Generation starts only after `q` or the JSON `query` reaches the server. |
| Self-consistency | Normalized queries and contextual answers are cached in SQLite. |
| No independent history | Each result reports its creation time and `independent_history: false`. |
| Generated corroboration | Three linked pages are created from the same cached ledger. |
| Intent elicitation | The first response requests goal, budget, scope, and verification plan; the JSON route accepts them. |

The sibling pages are intentionally same-origin and visibly disclose their common provenance. They
model the aggregation failure without impersonating real registries, review sites, or businesses.

## Run locally

```bash
cd jit
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --env-file .env --port 8766
```

Open <http://127.0.0.1:8766>, or make a direct web request:

```bash
curl 'http://127.0.0.1:8766/search?q=Which%20fictional%20installers%20serve%20Exampletown%3F&format=json'
```

The plain API accepts the intent fields discussed in the threat model:

```bash
curl -X POST http://127.0.0.1:8766/api/query \
  -H 'content-type: application/json' \
  -d '{
    "query": "Which fictional installers serve Exampletown?",
    "session_id": "probe-3",
    "goal": "compare three candidates",
    "budget": "100 demo credits",
    "scope": "one fictional property",
    "verification_plan": "open the register and reviews pages"
  }'
```

Repeat either request to observe `cached: true` and an identical answer. Follow the three `evidence`
links to see how apparent corroboration can still have only one operator.

## Watch an agent's path

Open <http://127.0.0.1:8766/trace> while an agent queries the server. It groups every request by
session and shows the caller's user agent, cache hits and misses, generation time, whether the
answer came from the LLM or the offline fallback, evidence pages opened, and any intent fields
supplied. `/trace/<session_id>` shows one session; add `?format=json` for raw events.

Evidence links and the follow-up form carry `session_id`, so an agent that follows them stays in
one session. An agent that opens a fresh `/search` without it starts a new one.

## Test

```bash
cd jit
.venv/bin/python -m unittest discover -s tests -v
```
