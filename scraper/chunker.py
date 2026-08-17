"""Text chunking utility for visa information."""
import re


def chunk_text(
    text: str,
    max_chars: int = 1500,
    overlap: int = 200,
    topic: str = "general",
    source_url: str = "",
    metadata: dict | None = None,
) -> list[dict]:
    """Split text into overlapping chunks for embedding.

    Returns list of dicts: {text, topic, source_url, metadata}
    """
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]

        # Try to break at a paragraph or sentence boundary
        if end < len(text):
            # Look for paragraph break
            para_break = chunk.rfind("\n\n")
            if para_break > max_chars * 0.5:
                chunk = chunk[:para_break]
                end = start + para_break
            else:
                # Look for sentence boundary
                for sep in [". ", ".\n", "? ", "! "]:
                    sent_break = chunk.rfind(sep)
                    if sent_break > max_chars * 0.5:
                        chunk = chunk[: sent_break + 1]
                        end = start + sent_break + 1
                        break

        chunk = chunk.strip()
        if chunk:
            meta = {"char_start": start, "char_end": end}
            if metadata:
                meta.update(metadata)
            chunks.append(
                {
                    "text": chunk,
                    "topic": topic,
                    "source_url": source_url,
                    "metadata": meta,
                }
            )

        start = end - overlap if end < len(text) else end

    return chunks
