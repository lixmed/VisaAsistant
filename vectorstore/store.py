"""pgvector store for visa information.

Provides insert, query, and country-existence checks.
"""
from __future__ import annotations

import json

from .db import get_conn, has_country_data
from .embeddings import embed_text, embed_batch


class VisaVectorStore:
    """Vector store for visa information chunks."""

    def is_scraped(self, country: str) -> bool:
        return has_country_data(country)

    def _ensure_index(self):
        """Create ivfflat index if table has enough rows and index doesn't exist."""
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM visa_chunks")
            count = cur.fetchone()[0]
            if count >= 30:
                cur.execute("""
                    DO $$ BEGIN
                        CREATE INDEX idx_visa_chunks_embedding
                            ON visa_chunks USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 10);
                    EXCEPTION WHEN duplicate_table THEN NULL;
                    END $$;
                """)
                conn.commit()

    def insert_chunks(
        self,
        country: str,
        chunks: list[dict],
    ) -> int:
        """Insert chunked visa data. Each dict: {text, topic, source_url?, metadata?}."""
        texts = [c["text"] for c in chunks]
        embeddings = embed_batch(texts)

        conn = get_conn()
        inserted = 0
        with conn.cursor() as cur:
            for i, chunk in enumerate(chunks):
                cur.execute(
                    """
                    INSERT INTO visa_chunks (country, topic, chunk_text, source_url, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        country.lower(),
                        chunk.get("topic", "general"),
                        chunk["text"],
                        chunk.get("source_url", ""),
                        json.dumps(chunk.get("metadata", {})),
                        embeddings[i],
                    ),
                )
                inserted += 1
            conn.commit()
        self._ensure_index()
        return inserted

    def query(
        self,
        country: str,
        question: str,
        top_k: int = 8,
    ) -> list[dict]:
        """Find the most relevant chunks for a country + question."""
        q_embedding = embed_text(question)
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_text, topic, source_url, metadata,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM visa_chunks
                WHERE country = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (q_embedding, country.lower(), q_embedding, top_k),
            )
            rows = cur.fetchall()
        return [
            {
                "text": r[0],
                "topic": r[1],
                "source_url": r[2],
                "metadata": r[3],
                "similarity": float(r[4]),
            }
            for r in rows
        ]

    def get_all_for_country(self, country: str) -> list[dict]:
        """Get all chunks for a country (for injecting into system prompt)."""
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chunk_text, topic, source_url FROM visa_chunks WHERE country = %s ORDER BY id",
                (country.lower(),),
            )
            rows = cur.fetchall()
        return [{"text": r[0], "topic": r[1], "source_url": r[2]} for r in rows]

    def clear_country(self, country: str) -> int:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM visa_chunks WHERE country = %s", (country.lower(),))
            deleted = cur.rowcount
            conn.commit()
        return deleted
