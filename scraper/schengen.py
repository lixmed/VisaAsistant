"""Schengen-specific scraper.

Scrapes VFS Global country pages and embassy sites for visa information.
Each Schengen country has a VFS Global page with specific requirements.
"""
from .base import fetch_page, ddgs_search
from .chunker import chunk_text

# VFS Global base URLs by country
VFS_COUNTRIES = {
    "italy": {"vfs_url": "https://visa.vfsglobal.com/egy/en/ita", "embassy": "https://ambcairo.esteri.it/en/servizi-consolari-e-visti/", "name": "Italy"},
    "france": {"vfs_url": "https://visa.vfsglobal.com/egy/en/fra", "embassy": "https://www.ambafrance-eg.org/", "name": "France"},
    "germany": {"vfs_url": "https://visa.vfsglobal.com/egy/en/deu", "embassy": "https://egypt.diplo.de/egy-en", "name": "Germany"},
    "spain": {"vfs_url": "https://visa.vfsglobal.com/egy/en/esp", "embassy": "https://www.exteriores.gob.es/Embajadas/cairo/en/", "name": "Spain"},
    "netherlands": {"vfs_url": "https://visa.vfsglobal.com/egy/en/nld", "embassy": "https://www.netherlandsandyou.nl/your-country-and-the-netherlands/egypt", "name": "Netherlands"},
    "austria": {"vfs_url": "https://visa.vfsglobal.com/egy/en/aut", "embassy": "https://www.bmeia.gv.at/en/", "name": "Austria"},
    "belgium": {"vfs_url": "https://visa.vfsglobal.com/egy/en/bel", "embassy": "https://diplobel.diplomatie.be/en", "name": "Belgium"},
    "czech republic": {"vfs_url": "https://visa.vfsglobal.com/egy/en/cze", "embassy": "https://www.mzv.cz/cairo/en/", "name": "Czech Republic"},
    "denmark": {"vfs_url": "https://visa.vfsglobal.com/egy/en/dnk", "embassy": "https://egypt.um.dk/en", "name": "Denmark"},
    "estonia": {"vfs_url": "https://visa.vfsglobal.com/egy/en/est", "embassy": "https://www.vm.ee/en", "name": "Estonia"},
    "finland": {"vfs_url": "https://visa.vfsglobal.com/egy/en/fin", "embassy": "https://finlandabroad.fi/en/", "name": "Finland"},
    "greece": {"vfs_url": "https://visa.vfsglobal.com/egy/en/grc", "embassy": "https://www.mfa.gr/cairo/en/", "name": "Greece"},
    "hungary": {"vfs_url": "https://visa.vfsglobal.com/egy/en/hun", "embassy": "https://abroad.kormany.hu/en/", "name": "Hungary"},
    "iceland": {"vfs_url": "https://visa.vfsglobal.com/egy/en/isl", "embassy": "https://www.government.is/ministries/ministry-for-foreign-affairs/", "name": "Iceland"},
    "latvia": {"vfs_url": "https://visa.vfsglobal.com/egy/en/lva", "embassy": "https://www.mfa.gov.lv/en", "name": "Latvia"},
    "liechtenstein": {"vfs_url": None, "embassy": "https://www.regierung.li/", "name": "Liechtenstein"},
    "lithuania": {"vfs_url": "https://visa.vfsglobal.com/egy/en/ltu", "embassy": "https://urm.lrv.lt/en/", "name": "Lithuania"},
    "luxembourg": {"vfs_url": "https://visa.vfsglobal.com/egy/en/lux", "embassy": "https://mae.public.lu/en.html", "name": "Luxembourg"},
    "malta": {"vfs_url": "https://visa.vfsglobal.com/egy/en/mlt", "embassy": "https://foreign.gov.mt/en/", "name": "Malta"},
    "norway": {"vfs_url": "https://visa.vfsglobal.com/egy/en/nor", "embassy": "https://www.regjeringen.no/en/", "name": "Norway"},
    "poland": {"vfs_url": "https://visa.vfsglobal.com/egy/en/pol", "embassy": "https://www.gov.pl/web/uae", "name": "Poland"},
    "portugal": {"vfs_url": "https://visa.vfsglobal.com/egy/en/prt", "embassy": "https://portal.mne.gov.pt/en/", "name": "Portugal"},
    "slovakia": {"vfs_url": "https://visa.vfsglobal.com/egy/en/svk", "embassy": "https://www.mzv.sk/en", "name": "Slovakia"},
    "slovenia": {"vfs_url": "https://visa.vfsglobal.com/egy/en/svn", "embassy": "https://www.gov.si/en/", "name": "Slovenia"},
    "sweden": {"vfs_url": "https://visa.vfsglobal.com/egy/en/swe", "embassy": "https://www.government.se/government-of-sweden/", "name": "Sweden"},
    "switzerland": {"vfs_url": "https://visa.vfsglobal.com/egy/en/che", "embassy": "https://www.eda.admin.ch/countries/egypt/en/home.html", "name": "Switzerland"},
}


def _topic_from_url(url: str) -> str:
    url = url.lower()
    if "document" in url or "requirement" in url:
        return "documents"
    if "fee" in url or "cost" in url or "price" in url:
        return "fees"
    if "appointment" in url or "book" in url:
        return "appointment"
    if "form" in url or "application" in url:
        return "application"
    if "process" in url or "time" in url:
        return "processing"
    return "general"


def scrape_schengen(country: str) -> list[dict]:
    """Scrape visa info for a Schengen country. Returns chunks for pgvector."""
    country = country.lower().strip()
    info = VFS_COUNTRIES.get(country)
    if not info:
        return []

    all_text = []
    source_urls = []

    # 1. VFS Global page
    if info["vfs_url"]:
        for page_path in ["", "/track-application", "/book-an-appointment"]:
            url = info["vfs_url"] + page_path
            text = fetch_page(url)
            if text and len(text) > 200:
                all_text.append(text[:5000])
                source_urls.append(url)
            import time; time.sleep(1)

    # 2. Embassy page
    if info["embassy"]:
        text = fetch_page(info["embassy"])
        if text and len(text) > 200:
            all_text.append(text[:5000])
            source_urls.append(info["embassy"])

    # 3. DuckDuckGo search for specific info
    queries = [
        f"Schengen visa {info['name']} requirements Egyptian citizens 2026",
        f"VFS Global {info['name']} visa fee Egypt appointment",
        f"{info['name']} Schengen visa processing time documents checklist",
    ]
    for q in queries:
        results = ddgs_search(q, max_results=3)
        for r in results:
            url = r.get("url", "")
            if any(bad in url for bad in ["youtube.com", "facebook.com", "twitter.com", "reddit.com"]):
                continue
            text = fetch_page(url)
            if text and len(text) > 200:
                all_text.append(text[:5000])
                source_urls.append(url)
                import time; time.sleep(1)

    # 4. Combine and chunk
    combined = "\n\n---\n\n".join(all_text)
    if not combined.strip():
        return []

    chunks = []
    for i, url in enumerate(source_urls):
        # Get the text for this specific source
        if i < len(all_text):
            source_chunks = chunk_text(
                all_text[i],
                topic=_topic_from_url(url),
                source_url=url,
                metadata={"country": country, "scrape_type": "schengen"},
            )
            chunks.extend(source_chunks)

    # Add combined overview chunk
    overview = chunk_text(
        f"Visa information for {info['name']} (Schengen area)\n\n{combined[:8000]}",
        topic="overview",
        source_url=info.get("vfs_url") or info.get("embassy", ""),
        metadata={"country": country, "scrape_type": "schengen_combined"},
    )
    chunks.extend(overview)

    return chunks
