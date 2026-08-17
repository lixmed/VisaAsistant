"""Search and knowledge-base tools the agent can call.

All tools return plain strings, ready to be injected into the LLM context.
Web search is free (DuckDuckGo) unless a Tavily API key is configured.
"""

import json
import re
import time

import requests

from .config import TAVILY_API_KEY, REQUEST_TIMEOUT, KNOWLEDGE_FILE

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def load_knowledge_base() -> dict:
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Could not load knowledge base: {e}"}


def _extract_text(html: str, max_chars: int = 2500) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars]


def _tavily_search(query: str, max_results: int = 5) -> list:
    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in resp.json().get("results", [])
    ]


def _ddgs_search(query: str, max_results: int = 5) -> list:
    from ddgs import DDGS

    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
            )
    return results


def search_web(query: str) -> str:
    """Search the web and return a compact list of results."""
    try:
        if TAVILY_API_KEY:
            results = _tavily_search(query)
        else:
            results = _ddgs_search(query)
    except Exception as e:
        return f"[search_web failed: {e}]"

    if not results:
        return "[search_web: no results found]"

    lines = []
    for i, r in enumerate(results, 1):
        snippet = (r.get("snippet") or "")[:180]
        lines.append(f"{i}. {r.get('title')}\n   URL: {r.get('url')}\n   {snippet}")
    return "\n\n".join(lines)


def fetch_page(url: str) -> str:
    """Fetch a web page and return its readable text content."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en,ar;q=0.8"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"[fetch_page failed for {url}: {e}]"
    return _extract_text(resp.text)


def search_knowledge_base(query: str) -> str:
    """Search the curated visa knowledge base and return matching entries."""
    kb = load_knowledge_base()
    if "error" in kb:
        return kb["error"]

    q = query.lower()
    tokens = re.findall(r"\b[a-z]{3,}\b", q)

    def score(entry: dict) -> int:
        blob = json.dumps(entry, ensure_ascii=False).lower()
        return sum(1 for t in tokens if t in blob)

    scored = [(score(e), e) for e in kb.get("visa_types", [])]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for s, e in scored if s > 0][:3] or [e for _, e in scored[:1]]

    facts = kb.get("key_facts_for_egyptians", {})
    routes = kb.get("egypt_application_routes", [])
    out = [
        "=== CURATED KNOWLEDGE BASE (baseline; always verify with official sources) ===",
        "Countries in the Schengen area: " + ", ".join(kb["countries"]["schengen_countries"]),
        kb["countries"].get("eu_non_schengen_notes", ""),
    ]
    for e in top:
        out.append("\n--- " + e.get("name", "") + " ---")
        for key in ("purpose", "suitability", "where_to_apply", "standard_fee", "processing_time", "validity", "notes"):
            if e.get(key):
                out.append(f"{key.replace('_', ' ').title()}: {e[key]}")
        reqs = e.get("main_requirements", {})
        if reqs:
            out.append("Document requirements:")
            for k, v in reqs.items():
                out.append(f"  - {k.replace('_', ' ').title()}: {v}")
        links = e.get("official_links") or []
        if links:
            out.append("Official links: " + ", ".join(links))
    out.append("\nApplication routes in Egypt:")
    for r in routes:
        out.append(f"- {r['name']} ({', '.join(r['countries_covered'])}): {r['url']} - {r['notes']}")
    out.append("\nKey facts for Egyptian applicants:")
    for k, v in facts.items():
        out.append(f"- {k.replace('_', ' ').title()}: {v}")
    out.append("\nDISCLAIMER: baseline data only. Fees/documents change - always verify current details on official sites.")
    return "\n".join(out)


if __name__ == "__main__":
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else "schengen tourist visa requirements for egyptian citizens"
    print("KB:", search_knowledge_base(arg)[:1500])
    print("\n---WEB---")
    print(search_web(arg)[:1500])
