# Readpath

> The race to be the first thing an agent reads: predictive prefetch, incentive risk and verification for agent-facing MCP servers.

A mid-latency Python MCP server with a database, a Jev-driven next-step predictor, and
pre-generated content pages that can be offered to brands as sponsored placements.

## Summary of the formal write-up
Full version: [`docs/formalization.tex`](docs/formalization.tex).

- **Model:** sessions are words over a tool alphabet; bait pairs are `professions x locations`.
  A predictor `pi(next | last, bait)` (Jev, or a Markov baseline) selects next steps with
  probability at least `tau`, and content for them is generated *before* the agent asks.
- **Analysis:** hit rate `H(tau)` = probability mass of prefetched steps; at most `1/tau`
  artifacts per bait; prefetch helps when generation time is less than the agent's gap between calls.
- **The issue:** the operator is paid by brands while the agent serves a user, a principal-agent
  problem. Pre-writing answers tuned to the agent is manipulation-capable, and undisclosed
  sponsorship is deceptive. The code therefore rejects agent-directed instructions, labels
  sponsored placement, and limits anonymous writes.

- **Race dynamics:** predictable call paths create a first-mover race on the agent's read path that
  favours fraud, since verification costs latency. As on-demand generation gets faster, per-step
  prefetch loses its edge and verification becomes the bottleneck; whole-intent submission is a
  proposed direction with its own privacy and auction costs (a projection, not measured).

- **Potential fix:** agents submit their whole intent once (goal, constraints, budget, verification
  requirement) and receive a signed plan with hash-pinned artifacts: one round trip, no prediction,
  closes the check/use gap. Planned as a future `submit_intent` tool + planner module; not implemented yet.

- **Jev's speed (unverified vendor claims):** 70-500 ms responses, $0.042/M input tokens
  ([heise](https://www.heise.de/en/news/AI-model-Jev-to-make-machines-decide-faster-11457071.html));
  "20-200x faster" ([Latent Space](https://www.latent.space/p/ainews-jev-a-system-one-model-that));
  developer reports of 5-20x vs. frontier LLMs, Gemini slightly more accurate
  ([TechCrunch](https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/));
  [announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev). No independent benchmark exists yet.
- **Generalization:** any model with accuracy >= a threshold and latency well under the agent's budget can sit in
  the read path; each 10x of speed at acceptable quality lets an operator pre-position more. So the risks follow
  the speed-quality frontier, not Jev, and defences belong on the receiving side.

## Architecture
| File | Role |
|---|---|
| `app/main.py` | FastAPI app, `/mcp` endpoint, latency floor, page serving, `/api/slots/.../offer` |
| `app/mcp.py` | JSON-RPC MCP tools: db read/list/write/delete, `find_providers`, `read_skill` |
| `app/pipeline.py` | Bait read -> predict -> generate -> claim domain -> go live |
| `app/jev.py` | Jev adapter (schema placeholder) with Markov fallback |
| `app/generator.py` | OpenAI-compatible content model + safety filter |
| `app/domains.py` | Domain pool, budgeted purchase (dry-run by default) |
| `scripts/decompose.py` | Generate baits; print tool-to-next-tool flows from logs |

## Run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in
python -m scripts.decompose baits --professions plumber --locations zurich
uvicorn app.main:app --port 8765
```

## Status / TODO
- Jev request schema is not public; adapt `_call_jev` once docs access exists.
- Registrar adapter for real domain purchases (disabled unless `ALLOW_PURCHASE=true`).
- `submit_intent` tool, planner and signing (see "Potential fix" in the write-up).
- Contacting the Muse (Meta) side: to be decided.
