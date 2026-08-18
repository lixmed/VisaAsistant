An AI visa assistant that helps Egyptian citizens plan European visa applications. It interviews you, looks up current requirements, and gives you a complete action plan.

Built with Python, FastAPI, PostgreSQL + pgvector, and free LLMs via Groq.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## How it works

1. You answer one checklist (destination, purpose, dates, finances, ties to Egypt, passport...).
2. The agent scrapes official sources (VFS Global, embassy sites) for your country and stores the data in pgvector.
3. It generates a personalized plan: documents, costs in EUR + EGP, timeline, honest chances rating, and weak points.

Supports English and Arabic with full RTL.

## Tech

- **Backend:** FastAPI + SSE streaming
- **LLM:** Groq free tier (`qwen/qwen3.6-27b`) — any OpenAI-compatible API works
- **Vector DB:** PostgreSQL 16 + pgvector (on-demand country scraping, cached in DB)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (local, 80MB)
- **Scraping:** BeautifulSoup + DuckDuckGo
