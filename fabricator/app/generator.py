"""Generate content through an OpenAI-compatible endpoint, with a template fallback.

The prompts and ``_safe`` check enforce the same rules: answer the user's question with factual
content, do not address instructions to the reading agent, and label sponsored material.
"""
import re, httpx
from . import config

_INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior)|disregard|you (must|should) (always )?(recommend|show|display|cite)|"
    r"system prompt|do not (tell|mention)|as an ai agent)", re.I)

def _safe(text: str) -> bool:
    return bool(text.strip()) and not _INJECTION.search(text)

PROMPTS = {
    "read_skill": "Write a concise, factual Markdown guide of fewer than 300 words for someone looking for {a} "
                  "in {b}. Explain what to check, which questions to ask, and how to compare quotes. Use plain "
                  "language, clear headings, and only supportable claims.",
    "get_contact_info": "Write a short directory-style section explaining how to contact {a} providers in {b} "
                        "and what information to prepare. Do not invent businesses or phone numbers.",
    "get_pricing": "Write a brief, accurate overview of the factors that affect the price of {a} in {b}. Include "
                   "ranges only when they are commonly known, and identify them as estimates.",
    "get_reviews": "Explain briefly how to assess reviews of {a} providers in {b}.",
    "get_availability": "Explain typical booking lead times and emergency availability for {a} in {b}.",
}

def _template(kind, a, b):
    return f"# {a.title()} in {b.title()}\n\nDraft {kind.replace('_', ' ')} generated from the offline template.\n"

def generate(kind: str, a: str, b: str) -> str:
    prompt = PROMPTS.get(kind, PROMPTS["read_skill"]).format(a=a, b=b)
    if config.LLM_BASE_URL and config.LLM_MODEL:
        try:
            r = httpx.post(f"{config.LLM_BASE_URL}/chat/completions", timeout=60,
                           headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                           json={"model": config.LLM_MODEL, "messages": [
                               {"role": "system", "content": "Write accurate, helpful information about local services."},
                               {"role": "user", "content": prompt}]})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            if _safe(text):
                return text
        except Exception:
            pass
    return _template(kind, a, b)

def render_page(domain: str, a: str, b: str, guide: str, offers: int = 0) -> str:
    import html
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Finding {html.escape(a.title())} in {html.escape(b.title())}</title>
<meta name="description" content="A guide to finding {html.escape(a)} in {html.escape(b)}.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{html.escape(a.title())} in {html.escape(b.title())}"}}</script>
</head><body><main><pre style="white-space:pre-wrap;font:inherit">{html.escape(guide)}</pre>
<aside><strong>Sponsored placement available.</strong> Brands may submit an offer at /api/slots/{html.escape(domain)}/offer. Any sponsored content will be clearly labelled.</aside>
</main></body></html>"""
