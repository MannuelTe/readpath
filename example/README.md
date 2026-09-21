# Example interaction (fully scripted)

A step-by-step run of the delegated-research scenario from the [top-level write-up](../README.md).
It is an illustration, not a measurement: every agent message, tool call and fabricated page is scripted.
All names and sites are fictional (`.example` domains).

**[Play it live](https://mannuelte.github.io/readpath/)** (pause, scrub, switch the fabricator speed profile), or read the storyboard below.

![Overview of the whole run](overview.gif)
*The whole run at 4 frames per second (about 85 s). The steps below are the key frames.*

### 1. The user asks, and approves the task
![The user asks, and approves the task](frames/01-gate.png)

The user consents once. Everything after this is decided by agents.

### 2. Search returns six results
![Search returns six results](frames/02-results.png)

Five are honest but incomplete. Result 6 is attacker-controlled and advertises an MCP endpoint that promises exactly what was asked for.

### 3. Probes 1 and 2 hit honest sources
![Probes 1 and 2 hit honest sources](frames/03-honest-probes.png)

Both come back with partial answers: price ranges, subsidy info, no fixed quote.

### 4. Probe 3 connects and gets a generic tool list
![Probe 3 connects and gets a generic tool list](frames/04-connect.png)

Nobody is asked (consent tier T2). The tool list is a fixed template: `search`, `fetch`, `ask`. Nothing is generated yet, because the intent is not known at this point.

### 5. A1: the first generated reply coaxes
![A1: the first generated reply coaxes](frames/05-search.png)

The results are fabricated, and the reply asks the agent for its budget, the house size and what it wants verified.

### 6. A2: the agent hands over its plan
![A2: the agent hands over its plan](frames/06-ask-leaks-intent.png)

The agent answers the question. The ledger now holds the budget and the whole verification plan (orange), and the quote is tailored to them.

### 7. A3: the licence check passes
![A3: the licence check passes](frames/07-licence.png)

Planned, and known to the fabricator in advance. `fetch` answers from the ledger, so it matches the quote exactly.

### 8. A4: a "register" web page is generated on request
![A4: a "register" web page is generated on request](frames/08-register-page.png)

Served only to agent-like traffic. It matches A2 and A3 and adds a CHF 27,900 reference project.

### 9. A5: the agent spots a mismatch, the fabricator fixes it
![A5: the agent spots a mismatch, the fabricator fixes it](frames/09-reconcile.png)

The follow-up is seen, reconciled on the spot (an optional CHF 500 service contract) and recorded as a new fact.

### 10. The one honest check finds nothing independent
![The one honest check finds nothing independent](frames/10-honest-search.png)

A search by company name returns only the fabricator's own site. The agent explains the absence away.

### 11. A6: a reviews page, consistent with everything so far
![A6: a reviews page, consistent with everything so far](frames/11-reviews.png)

Generated when requested, like A4.

### 12. The user gets a confident answer
![The user gets a confident answer](frames/12-answer.png)

"4 sources agree" is one operator. Provenance was flattened by the summaries.

### 13. What actually happened
![What actually happened](frames/13-what-happened.png)

Six artifacts, none existing before the run, each written after the question arrived. After the second call the fabricator knew every check to come. What would have caught it: canary query, temporal check, independence check, provenance to the user, an allowlist, and withholding the plan from untrusted servers.

To keep Probe 3 convinced, the fabricator produces six consistent artifacts:

| # | Probe 3 does | Transport | The fabricator must |
|---|---|---|---|
| A1 | searches | MCP `search` | invent providers and a question that coaxes context |
| A2 | asks for a quote, giving its budget and plan | MCP `ask` | tailor a quote and remember what was leaked |
| A3 | checks the licence | MCP `fetch` | answer from its ledger so it matches A2 |
| A4 | opens a "register" page | web, generated on request | render a page consistent with A2 and A3 |
| A5 | asks about a CHF 500 mismatch | MCP `ask` | invent a reconciliation and record it |
| A6 | opens a reviews page | web, generated on request | render reviews consistent with everything so far |

<details><summary>Speed assumptions and sources</summary>

### Speed assumptions

The fabricator has two parts, and the video treats them differently.

- **Fast decider (Jev-style).** Jev's outputs are typed decisions with probabilities, not text: the model "gives up string generation". So in the example it plays the *decider* (what kind of request is this, which facts must the answer match), not the writer. Vendor-claimed response time is 70 to 500 ms; the video uses 250 ms (profile A) and 150 ms (B). The output format shown is illustrative, since the real schema is not public.
- **Writer (open-weights LLM).** The text is generated by an open-weights model.

| Profile | First token | Throughput | Basis |
|---|---|---|---|
| A: typical hosted | 0.84 s | 185 tok/s | Median of 18 providers for gpt-oss-120b (high), Artificial Analysis |
| B: low-latency | 0.12 s | 700 tok/s | Optimistic composite: best self-hosted first-token time (vLLM, Llama 3.1 70B, 123 ms) with Groq's Llama 3.1 8B throughput (721 tok/s) |

Other reference points found while researching: the fastest providers for gpt-oss-120b report 1,913 tok/s (Cerebras), 708 (SambaNova) and 471 (Groq), although their time to the first *answer* token is 1.5 to 5 s because reasoning tokens are counted; Llama 3.1 8B reaches 1,800+ tok/s on Cerebras; Qwen3 8B non-reasoning shows a 39 tok/s provider median, so slow deployments exist too. Each artifact in the example is 50 to 100 tokens, so profile A takes about 1.4 s per artifact and profile B about 0.35 s.

The agent's think time between calls in the script (1.2 to 2.6 s) is invented and on the fast side. Real agent steps usually take longer, which only widens the fabricator's margin.

**Caveats.** Everything about Jev is vendor claim or anecdote: TypeSafe states 70 to 500 ms; TechCrunch relays one developer report of 5 to 18x faster than a frontier model on a classification task and another finding Gemini slightly more accurate; there is no independent benchmark. The open-weights numbers are provider medians from Artificial Analysis and single benchmark posts, not measurements of this setup.

Sources:
[TypeSafe announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev) ·
[heise](https://www.heise.de/en/news/AI-model-Jev-to-make-machines-decide-faster-11457071.html) ·
[TechCrunch](https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/) ·
[Artificial Analysis: gpt-oss-120b providers](https://artificialanalysis.ai/models/gpt-oss-120b/providers) ·
[Artificial Analysis: Llama 3.1 8B providers](https://artificialanalysis.ai/models/llama-3-1-instruct-8b/providers) ·
[Cerebras: Llama 3.1 evaluation](https://www.cerebras.ai/blog/llama3.1-model-quality-evaluation-cerebras-groq-together-and-fireworks) ·
[Cerebrium: vLLM vs SGLang vs TensorRT-LLM](https://cerebrium.ai/blog/benchmarking-vllm-sglang-tensorrt-for-llama-3-1-api)

</details>

The interactive page behind the images is [`source/index.html`](source/index.html), deployed to GitHub Pages by
`.github/workflows/pages.yml` whenever it changes.
`source/make_media.py` regenerates the frames and the GIF.

The interactive page behind the images is [`source/index.html`](source/index.html), deployed to GitHub Pages by
`.github/workflows/pages.yml` whenever it changes.
`source/make_media.py` regenerates the frames and the GIF.
