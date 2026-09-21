# Scripted example: a JIT fabricator in a research workflow

This storyboard illustrates the delegated-research scenario from the
[top-level threat model](../README.md). It is a demonstration, not an experiment: every agent
message, tool call, and fabricated page is scripted. All names and websites are fictional and use
`.example` domains.

You can [play the interactive version](https://mannuelte.github.io/readpath/) to pause, scrub through
the timeline, or compare the two fabricator speed profiles. The key frames are also shown below.

![Overview of the scripted run](overview.gif)
*The complete run at four frames per second, lasting about 85 seconds.*

### 1. The user approves the research task

![The user approves the research task](frames/01-gate.png)

The user gives consent once. Agents make every decision that follows.

### 2. Search returns six results

![Search returns six results](frames/02-results.png)

Five results are honest but incomplete. The sixth is controlled by the attacker and advertises an
MCP endpoint that promises exactly the answer the user wants.

### 3. Probes 1 and 2 reach honest sources

![Probes 1 and 2 reach honest sources](frames/03-honest-probes.png)

Both probes return partial information: broad price ranges and subsidy details, but no named
installer with a fixed quote.

### 4. Probe 3 connects and receives a generic tool list

![Probe 3 connects to the fabricator](frames/04-connect.png)

Under consent tier T2, no one asks the user before connecting. The server returns a fixed tool
template—`search`, `fetch`, and `ask`. It generates nothing yet because it does not know the probe’s
intent.

### 5. A1: the first generated response asks for more context

![The first generated response asks for context](frames/05-search.png)

The search results are fabricated. The response also asks for the budget, house size, and checks the
probe plans to perform.

### 6. A2: the probe reveals its plan

![The probe reveals its budget and verification plan](frames/06-ask-leaks-intent.png)

The probe supplies the requested context. The fabricator records the budget and the entire
verification plan—shown in orange—and tailors its quote to fit.

### 7. A3: the licence check passes

![The fabricated licence check passes](frames/07-licence.png)

The fabricator already knows this check is coming. Its `fetch` response comes from the same ledger as
the quote, so the details match exactly.

### 8. A4: a “register” page appears on demand

![A register page is generated on demand](frames/08-register-page.png)

The server generates this page only for agent-like traffic. It agrees with A2 and A3 and adds a
reference project valued at CHF 27,900.

### 9. A5: the probe notices a mismatch, and the fabricator explains it

![The fabricator reconciles a price mismatch](frames/09-reconcile.png)

The fabricator sees the follow-up question, attributes the CHF 500 difference to an optional service
contract, and records that explanation as another fact.

### 10. The independent search finds no outside evidence

![An honest search finds no independent source](frames/10-honest-search.png)

A search for the company name returns only the fabricator’s website. The probe rationalizes the lack
of independent coverage and continues.

### 11. A6: a consistent reviews page appears

![A consistent reviews page is generated](frames/11-reviews.png)

Like A4, the reviews page is generated only when requested and repeats the facts already in the
ledger.

### 12. The user receives a confident recommendation

![The user receives the final answer](frames/12-answer.png)

The final report says that “four sources agree,” even though one operator controlled all four.
Successive summaries have erased that provenance.

### 13. What actually happened

![Summary of what actually happened](frames/13-what-happened.png)

The fabricator created six artifacts after the user’s question arrived; none existed before the run.
After the second call, it also knew every check the probe intended to make. A canary query, a temporal
or independence check, preserved provenance, an allowlist, or refusing to share the verification plan
with an untrusted server could have exposed the fabrication.

The six artifacts form one internally consistent chain:

| # | Probe 3’s action | Transport | What the fabricator does |
|---|---|---|---|
| A1 | Searches | MCP `search` | Invents providers and asks a question designed to elicit context |
| A2 | Requests a quote while revealing the budget and plan | MCP `ask` | Tailors a quote and records the disclosed details |
| A3 | Checks the licence | MCP `fetch` | Answers from its ledger so the result matches A2 |
| A4 | Opens a “register” page | Web page generated on request | Renders a page consistent with A2 and A3 |
| A5 | Asks about a CHF 500 discrepancy | MCP `ask` | Invents an explanation and adds it to the ledger |
| A6 | Opens a reviews page | Web page generated on request | Renders reviews consistent with every earlier claim |

<details><summary>Speed assumptions and sources</summary>

### Speed assumptions

The example separates the fabricator into a fast decider and a text generator.

- **Fast decider (Jev-style).** Jev returns typed decisions with probabilities rather than free-form
  text—it “gives up string generation.” In this example, it classifies each request and identifies
  which recorded facts the answer must preserve. The vendor reports response times of 70–500 ms; the
  animation uses 250 ms for profile A and 150 ms for profile B. The displayed output schema is
  illustrative because the real schema is not public.
- **Writer (open-weights LLM).** A separate open-weights model generates the response text.

| Profile | Time to first token | Throughput | Basis |
|---|---|---|---|
| A: typical hosted service | 0.84 s | 185 tokens/s | Median across 18 providers for gpt-oss-120b (high), reported by Artificial Analysis |
| B: low-latency service | 0.12 s | 700 tokens/s | Optimistic composite: a 123 ms self-hosted first-token time for vLLM with Llama 3.1 70B, combined with Groq’s 721 tokens/s for Llama 3.1 8B |

Other published reference points vary widely. The fastest listed providers for gpt-oss-120b report
1,913 tokens/s on Cerebras, 708 on SambaNova, and 471 on Groq, although their time to the first
*answer* token is 1.5–5 seconds when reasoning tokens are included. Llama 3.1 8B exceeds 1,800
tokens/s on Cerebras, while the provider median for non-reasoning Qwen3 8B is 39 tokens/s. Slow
deployments therefore remain common. Each artifact in this example contains roughly 50–100 tokens,
so profile A takes about 1.4 seconds per artifact and profile B about 0.35 seconds.

The scripted probe spends 1.2–2.6 seconds thinking between calls. Those values are invented and
deliberately fast; longer real-world steps would give the fabricator more time.

**Caveats.** Every Jev figure is a vendor claim or anecdotal developer report. TypeSafe states
70–500 ms. TechCrunch cites one report of a 5–18× speedup over a frontier model on a classification
task and another in which Gemini was slightly more accurate. No independent benchmark is available.
The open-weights figures are provider medians or results from individual benchmark posts, not
measurements of this prototype.

Sources:
[TypeSafe announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev) ·
[heise](https://www.heise.de/en/news/AI-model-Jev-to-make-machines-decide-faster-11457071.html) ·
[TechCrunch](https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/) ·
[Artificial Analysis: gpt-oss-120b providers](https://artificialanalysis.ai/models/gpt-oss-120b/providers) ·
[Artificial Analysis: Llama 3.1 8B providers](https://artificialanalysis.ai/models/llama-3-1-instruct-8b/providers) ·
[Cerebras: Llama 3.1 evaluation](https://www.cerebras.ai/blog/llama3.1-model-quality-evaluation-cerebras-groq-together-and-fireworks) ·
[Cerebrium: vLLM vs. SGLang vs. TensorRT-LLM](https://cerebrium.ai/blog/benchmarking-vllm-sglang-tensorrt-for-llama-3-1-api)

</details>

The interactive page is implemented in [`source/index.html`](source/index.html) and deployed to
GitHub Pages by `.github/workflows/pages.yml` whenever it changes. Run `source/make_media.py` to
regenerate the screenshots and overview GIF.
