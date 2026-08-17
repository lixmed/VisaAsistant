<div align="center">

# Veeza AI

**Your AI visa assistant for European visas — built for Egyptians**

Interview -> research -> **a complete application plan** (documents, costs in EUR & EGP, timeline, chances, sources) — powered by free models + pgvector RAG.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-vector%20search-4169E1)](https://github.com/pgvector/pgvector)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Free%20Tier-f55036?logo=groq&logoColor=white)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## What it does

An end-to-end **AI agent** that guides an Egyptian applicant through a European visa application:

1. **Interviews you** — one batched checklist covering everything (purpose, destination, dates, income, ties to Egypt, passport...). One reply gets you a complete plan.
2. **Researches via pgvector RAG** — scrapes official sources (VFS Global, embassies), stores in PostgreSQL + pgvector, and reads pre-chunked context. No live web search loops — fast and token-efficient.
3. **Builds your plan** — a structured, personalised plan with a step-by-step process, document checklist, estimated costs (EUR + live EGP conversion), timeline, official sources, and an honest approval-likelihood assessment with weak points.

Answers in **English or Arabic**. UI is **fully bilingual with RTL support**.

### vs. Paid concierge services

| Typical concierge services | **Veeza AI** |
|---|---|
| Paid, per-application fees | **Free**, research-first assistant |
| "We guarantee nothing" | Honest **likelihood rating + specific weak points** |
| Fixed package prices | **Live cost estimate in EUR and EGP** |
| No transparency on sources | Every plan cites **official sources** you can click |
| Chatbot with no agentic loop | **Tool-calling agent** + pgvector RAG |

---

## Architecture

```
User picks country
        |
        v
  ensure_country_data(country)
        |
  +-----+------+
  |             |
  v             v
Scrape VFS    DuckDuckGo
+ embassy     search
  |             |
  +------+------+
         |
         v
  Chunk text (1500 chars, overlap)
         |
         v
  Embed (all-MiniLM-L6-v2, 384-dim)
         |
         v
  Store in PostgreSQL + pgvector
         |
         v
  lookup_visa(country, topic)
         |
         v
  Top 8 relevant chunks -> LLM context
         |
         v
  Agent generates plan (no web search tools needed)
```

### Key components

| Component | Description |
|---|---|
| `vectorstore/` | PostgreSQL + pgvector connection, embeddings, similarity search |
| `scraper/schengen.py` | Schengen-specific scraper (26 countries: VFS Global + embassy + DuckDuckGo) |
| `scraper/dynamic.py` | Generic scraper for any country (Ireland, UK, etc.) |
| `backend/rag.py` | Orchestrator: scrape -> embed -> store -> query |
| `backend/agent.py` | Agent loop with `ensure_country_data` + `lookup_visa` tools |
| `data/visa_programs.json` | Curated Egypt-specific baseline knowledge base |

### Why pgvector instead of live web search?

| Live web search (old) | pgvector RAG (current) |
|---|---|
| 3-5 tool calls per request | 1 lookup call |
| ~12,000-20,000 tokens/turn | ~4,000-6,000 tokens/turn |
| Hits 8K TPM free tier cap | Comfortably under |
| ~30s per request (web fetch) | ~1s cache hit (subsequent) |
| Non-deterministic results | Consistent, deterministic |

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| LLM | OpenAI-compatible SDK, Groq free tier (`qwen/qwen3.6-27b`) |
| Vector DB | PostgreSQL 16 + pgvector |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 80MB, CPU) |
| Scraping | requests + BeautifulSoup + DuckDuckGo |
| Exchange rate | Frankfurter / open.er-api (free, ECB data) |
| Frontend | Vanilla HTML/CSS/JS, English + Arabic (RTL) |

---

## Repository structure

```
veezaAI/
├── app.py                 # Hugging Face Spaces / Docker entrypoint
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker / HF Spaces image
├── docker-compose.yml     # PostgreSQL + pgvector + app
├── run.py                 # Local dev launcher (port 8000)
├── backend/
│   ├── app.py             # FastAPI: SSE chat, health, rate, knowledge, static
│   ├── agent.py           # Tool-calling agent loop (interview -> plan)
│   ├── rag.py             # pgvector RAG orchestrator
│   ├── tools.py           # search_knowledge_base
│   ├── exchange.py        # Live EUR->EGP rate
│   └── config.py          # Settings from env / .env
├── vectorstore/
│   ├── __init__.py
│   ├── db.py              # PostgreSQL connection
│   ├── embeddings.py      # Local sentence-transformers model
│   └── store.py           # pgvector insert, query, country check
├── scraper/
│   ├── __init__.py
│   ├── base.py            # HTTP requests, DuckDuckGo search
│   ├── schengen.py        # Schengen-specific scraper (26 countries)
│   ├── dynamic.py         # Generic scraper for any country
│   └── chunker.py         # Text chunking utility
├── db/
│   └── init.sql           # PostgreSQL schema (visa_chunks table + indexes)
├── data/
│   └── visa_programs.json # Curated Egypt-specific visa knowledge base
├── frontend/
│   ├── index.html         # Chat UI + plan panel
│   ├── style.css          # Styles, RTL + print/PDF
│   └── app.js             # SSE streaming, i18n, checklist, history, EGP
├── .env.example           # Copy to .env and fill in your key
└── LICENSE
```

---

## Quickstart (local)

Requires **Python 3.12+**, **PostgreSQL 16+** (with pgvector extension), and a free **Groq API key**.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL + pgvector

Make sure PostgreSQL is running, then create the database:

```bash
# Connect as superuser
psql -U postgres

# Create user and database
CREATE USER veeza WITH PASSWORD '1234' CREATEDB;
CREATE DATABASE veeza OWNER veeza;
\q

# Enable pgvector and create schema
psql -U veeza -d veeza -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U veeza -d veeza -f db/init.sql
```

### 3. Configure

```bash
cp .env.example .env
# Set LLM_API_KEY=<your Groq key> in .env
# DATABASE_URL defaults to postgresql://veeza:1234@localhost:5432/veeza
```

### 4. Run

```bash
python run.py
```

Open **http://127.0.0.1:8000** and start chatting.

---

## Docker

```bash
# Full stack (PostgreSQL + app)
docker compose up --build
```

Open **http://localhost:7860**.

The first time a user picks a country, the scraper runs and caches results in pgvector. Subsequent requests for that country are instant.

---

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `LLM_API_KEY` | — | **Required.** Groq / OpenRouter / any OpenAI-compatible key |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | Override for OpenRouter etc. |
| `LLM_MODEL` | `qwen/qwen3.6-27b` | Must support function calling |
| `DATABASE_URL` | `postgresql://veeza:1234@localhost:5432/veeza` | PostgreSQL connection string |
| `TAVILY_API_KEY` | empty | Optional; not currently used with pgvector flow |

**Model tips:** `qwen/qwen3.6-27b` (default) is fast with good Arabic and reliable tool calling. The agent batches the whole interview into one checklist and keeps research lean — comfortably under the Groq free tier (30 RPM / 8K TPM / 200K TPD).

---

## API

| Endpoint | Description |
|---|---|
| `POST /api/chat/stream` | SSE stream. Body: `{session_id?, message}` -> events `{type: "status"|"question"|"message"|"plan"}` |
| `POST /api/chat` | Non-streaming. Returns `{session_id, reply, kind, plan}` |
| `POST /api/reset` | `{session_id}` -> clears a conversation |
| `GET /api/rate` | `{eur_to_egp}` — live EUR->EGP rate |
| `GET /api/knowledge` | The curated knowledge base |
| `GET /api/health` | `{status, model, base_url}` |

`kind: "question"` means the agent is waiting for your answer. `kind: "plan"` includes the full structured plan.

---

## Deploy to GitHub

```bash
# Stage everything (excluding .env)
git add .

# Commit
git commit -m "feat: pgvector RAG, Schengen scrapers, on-demand country scraping"

# Set main branch
git branch -M main

# Add remote (replace <your-username> and <your-repo>)
git remote add origin https://github.com/<your-username>/<your-repo>.git

# Push
git push -u origin main
```

## Deploy to Hugging Face Spaces

1. Create a **Docker** SDK Space at https://huggingface.co/new-space (name it e.g. `veeza-ai`).
2. Add the remote and push:

```bash
git remote add space https://huggingface.co/spaces/<your-username>/veeza-ai
git push space main
```

3. In **Space Settings -> Variables and secrets**, add:
   - `LLM_API_KEY` = your Groq key
   - `DATABASE_URL` = your PostgreSQL connection string (or add a PostgreSQL add-on)

The `Dockerfile` listens on port **7860** (HF's default).

> The `.gitignore` excludes `.env` — your API key never gets committed.

---

## License

[MIT](LICENSE).

This tool aggregates public information for research and planning only. It is **not legal advice** and does **not** guarantee visa approval. Fees, documents and procedures change — always confirm on the official embassy / visa-centre website before paying or submitting anything.
