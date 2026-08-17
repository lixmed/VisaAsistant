"""Dynamic scraper for any country.

Falls back to DuckDuckGo search + page fetch for countries
not covered by the Schengen-specific scraper.
"""
from .base import fetch_page, ddgs_search
from .chunker import chunk_text


def scrape_dynamic(country: str) -> list[dict]:
    """Scrape visa info for any country via web search.

    Works for Ireland, UK, and any non-Schengen destination.
    Returns chunks for pgvector.
    """
    country = country.lower().strip()
    all_chunks = []

    queries = [
        f"{country} visa requirements Egyptian citizens 2026",
        f"{country} work visa application process Egypt",
        f"{country} visa fees documents checklist Egyptian passport",
        f"how to apply {country} visa from Egypt VFS TLS",
        f"{country} visa processing time embassy Cairo",
    ]

    seen_urls = set()
    for q in queries:
        results = ddgs_search(q, max_results=3)
        for r in results:
            url = r.get("url", "")
            if url in seen_urls:
                continue
            if any(bad in url for bad in ["youtube.com", "facebook.com", "twitter.com", "reddit.com", "pinterest.com"]):
                continue
            seen_urls.add(url)

            text = fetch_page(url)
            if text and len(text) > 300:
                topic = "general"
                low_url = url.lower()
                if "document" in low_url or "requirement" in low_url:
                    topic = "documents"
                elif "fee" in low_url or "cost" in low_url:
                    topic = "fees"
                elif "process" in low_url or "time" in low_url:
                    topic = "processing"
                elif "appointment" in low_url or "vfs" in low_url or "tls" in low_url:
                    topic = "appointment"

                chunks = chunk_text(
                    text,
                    topic=topic,
                    source_url=url,
                    metadata={"country": country, "scrape_type": "dynamic"},
                )
                all_chunks.extend(chunks)

    # Add a combined overview if we found enough data
    if all_chunks:
        combined_text = f"Visa information for {country}\n\n"
        combined_text += "\n\n".join(c["text"][:1000] for c in all_chunks[:10])
        overview_chunks = chunk_text(
            combined_text[:8000],
            topic="overview",
            metadata={"country": country, "scrape_type": "dynamic_combined"},
        )
        all_chunks.extend(overview_chunks)

    return all_chunks
