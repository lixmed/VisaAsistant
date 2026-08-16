"""Hugging Face Spaces / Docker entrypoint for Veeza AI.

Runs the FastAPI backend (serves both the API and the frontend).
On HF Spaces, set the LLM_API_KEY secret in the Space settings.
"""

from backend.app import app  # noqa: F401
