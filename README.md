# Veeza AI

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

## Run locally

```bash
pip install -r requirements.txt

# Set up PostgreSQL
psql -U postgres -c "CREATE USER veeza WITH PASSWORD '1234' CREATEDB;"
psql -U postgres -c "CREATE DATABASE veeza OWNER veeza;"
psql -U veeza -d veeza -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U veeza -d veeza -f db/init.sql

# Configure
cp .env.example .env
# Add your Groq API key to .env

# Run
python run.py
```

Open http://127.0.0.1:8000

## Docker

```bash
docker compose up --build
```

Opens at http://localhost:7860

## Config

| Variable | Default | Description |
|---|---|---|
| `LLM_API_KEY` | — | Your Groq API key (free at console.groq.com) |
| `LLM_MODEL` | `qwen/qwen3.6-27b` | Model to use |
| `DATABASE_URL` | `postgresql://veeza:1234@localhost:5432/veeza` | PostgreSQL connection |

## API

| Endpoint | Description |
|---|---|
| `POST /api/chat/stream` | SSE stream (status/question/message/plan events) |
| `POST /api/chat` | Non-streaming response |
| `POST /api/reset` | Clear a session |
| `GET /api/health` | Health check |
| `GET /api/rate` | Live EUR to EGP rate |

## Push to GitHub

```bash
git add .
git commit -m "your message"
git remote add origin https://github.com/lixmed/VisaAsistant.git
git push -u origin main
```

## License

MIT. Not legal advice — always verify requirements on official embassy websites.
