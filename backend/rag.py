"""Orchestrator: scrape → embed → store for a given country.

Called by the agent when a country is first encountered.
"""
from __future__ import annotations

from scraper import scrape_schengen, scrape_dynamic
from vectorstore import VisaVectorStore

# All 26 Schengen area countries (plus Switzerland)
SCHENGEN_COUNTRIES = {
    "austria", "belgium", "croatia", "czech republic", "czechia",
    "denmark", "estonia", "finland", "france", "germany", "greece",
    "hungary", "iceland", "italy", "latvia", "liechtenstein",
    "lithuania", "luxembourg", "malta", "netherlands", "norway",
    "poland", "portugal", "slovakia", "slovenia", "spain",
    "sweden", "switzerland",
}

_store: VisaVectorStore | None = None


def _get_store() -> VisaVectorStore:
    global _store
    if _store is None:
        _store = VisaVectorStore()
    return _store


def ensure_country_data(country: str) -> dict:
    """Ensure visa data for a country is scraped and stored.

    Returns:
        {scraped: bool, chunks: int, source: "schengen"|"dynamic"}
    """
    store = _get_store()
    country = country.lower().strip()

    if store.is_scraped(country):
        return {"scraped": True, "chunks": len(store.get_all_for_country(country)), "source": "cache"}

    is_schengen = country in SCHENGEN_COUNTRIES or country.replace(" ", "") in {c.replace(" ", "") for c in SCHENGEN_COUNTRIES}

    if is_schengen:
        chunks = scrape_schengen(country)
    else:
        chunks = scrape_dynamic(country)

    if chunks:
        inserted = store.insert_chunks(country, chunks)
        return {"scraped": True, "chunks": inserted, "source": "schengen" if is_schengen else "dynamic"}

    return {"scraped": False, "chunks": 0, "source": "none"}


def lookup_visa_info(country: str, topic: str = "general") -> str:
    """Look up visa info for a country from pgvector.

    Returns formatted text suitable for LLM context injection.
    """
    store = _get_store()
    country = country.lower().strip()

    if not store.is_scraped(country):
        return f"[No visa data available for {country}. You may need to search the web.]"

    chunks = store.query(country, topic, top_k=8)
    if not chunks:
        return f"[No relevant visa data found for {country} on topic: {topic}]"

    parts = [f"=== Visa Information: {country.title()} ==="]
    for i, c in enumerate(chunks, 1):
        parts.append(f"\n--- Source {i} ({c['topic']}, similarity: {c['similarity']:.2f}) ---")
        parts.append(c["text"][:1500])
        if c.get("source_url"):
            parts.append(f"URL: {c['source_url']}")

    return "\n".join(parts)
