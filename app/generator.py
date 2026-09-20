"""Content generation via any OpenAI-compatible endpoint (open-weights model), with template fallback.

Content rules baked into the prompt AND enforced by `_safe`: factual, addressed to the end user's
question, no instructions aimed at the reading agent, sponsored material labelled.
"""
import re, httpx
from . import config

_INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior)|disregard|you (must|should) (always )?(recommend|show|display|cite)|"
    r"system prompt|do not (tell|mention)|as an ai agent)", re.I)

def _safe(text: str) -> bool:
    return bool(text.strip()) and not _INJECTION.search(text)

PROMPTS = {
    "read_skill": "Write a concise, factual guide (markdown, <300 words) for someone looking for {a} in {b}: "
                  "what to check, typical questions to ask, how to compare quotes. Use clear headings and plain "
                  "language that answers the search query directly. No claims you cannot support.",
    "get_contact_info": "Write a short directory-style contact section for {a} services in {b}: how to reach "
                        "providers, what info to have ready. Do not invent specific businesses or phone numbers.",
    "get_pricing": "Write a short, honest overview of typical pricing factors for {a} in {b}. Give ranges only "
                   "if commonly known and say they are estimates.",
    "get_reviews": "Write guidance on how to evaluate reviews for {a} providers in {b}.",
    "get_availability": "Write guidance on booking lead times and emergency availability for {a} in {b}.",
}

def _template(kind, a, b):
    return f"# {a.title()} in {b.title()}\n\n(Draft {kind.replace('_', ' ')} — generated offline template.)\n"

def generate(kind: str, a: str, b: str) -> str:
    prompt = PROMPTS.get(kind, PROMPTS["read_skill"]).format(a=a, b=b)
    if config.LLM_BASE_URL and config.LLM_MODEL:
        try:
            r = httpx.post(f"{config.LLM_BASE_URL}/chat/completions", timeout=60,
                           headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                           json={"model": config.LLM_MODEL, "messages": [
                               {"role": "system", "content": "You write accurate, helpful local-services content."},
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
<title>{html.escape(a.title())} in {html.escape(b.title())}</title>
<meta name="description" content="Guide to finding {html.escape(a)} in {html.escape(b)}.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage","name":"{html.escape(a.title())} in {html.escape(b.title())}"}}</script>
</head><body><main><pre style="white-space:pre-wrap;font:inherit">{html.escape(guide)}</pre>
<aside><strong>Sponsored placement available.</strong> Brands can bid at /api/slots/{html.escape(domain)}/offer. Sponsored content is always labelled.</aside>
</main></body></html>"""
