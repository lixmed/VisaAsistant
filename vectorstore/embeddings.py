"""Local embedding model for pgvector.

Uses sentence-transformers/all-MiniLM-L6-v2 (80MB, 384-dim, CPU-only).
Model is downloaded once and cached locally.
"""
import os
import threading

_model = None
_lock = threading.Lock()
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                cache = os.path.join(os.path.expanduser("~"), ".cache", "veeza_embeddings")
                _model = SentenceTransformer(_MODEL_NAME, cache_folder=cache)
    return _model


def embed_text(text: str) -> list:
    model = _get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list) -> list:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True).tolist()
