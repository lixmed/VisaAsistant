<div align="center">

# 🛂 Veeza AI

**Your AI visa assistant for Europeans visas — built for Egyptians 🇪🇬 → 🇪🇺**

Interview → research → **a complete application plan** (documents, costs in EUR & EGP, timeline, chances, sources) — powered by free models.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20GPT--OSS%20120B-f55036?logo=groq&logoColor=white)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Hugging Face](https://img.shields.io/badge/Hosted%20on-Hugging%20Face%20Spaces-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces)
[![Made in Egypt 🇪🇬](https://img.shields.io/badge/Made%20in-Egypt-white?labelColor=%23C09300)](https://en.wikipedia.org/wiki/Egypt)

</div>

---

## ✨ What it does

An end-to-end **AI agent** that guides an Egyptian applicant through a European visa application:

1. **Interviews you** — one natural question at a time (purpose, destination, dates, income, ties to Egypt, passport…).
2. **Researches live** — searches the web and reads **official sources** (embassies, VFS Global, TLScontact, EU Commission) for the current requirements, fees and procedures for *your* case.
3. **Builds your plan** — a structured, personalised plan with a step-by-step process, document checklist, estimated costs (**EUR + live EGP conversion**), timeline, official sources, and an honest approval-likelihood assessment with your weak points.

It answers in **English or Arabic**, and the UI is **fully bilingual with RTL support**.

### Difference vs. typical paid "we do it for you" services

| Typical concierge services | **Veeza AI** |
|---|---|
| Paid, per-application fees | **Free**, research-first assistant |
| "We guarantee nothing" | Honest **likelihood rating + specific weak points** to fix |
| Fixed package prices | **Live cost estimate in EUR and EGP** for your exact trip |
| No transparency on sources | Every plan cites **official sources** you can click |
| Chatbot with no agentic loop | **Tool-calling agent** that searches, reads pages and plans |

---

## 🎥 Demo

> Screenshot coming soon — add `screenshots/demo.png` (chat view) and `screenshots/plan.png` (plan panel) and they'll render here.

| Chat interview | Personalised plan |
|---|---|
| ![](screenshots/demo.png) | ![](screenshots/plan.png) |

---

## 🧠 How it works

The core is a **tool-calling agent loop** (`backend/agent.py`):

```
┌────────────┐   user message    ┌──────────────────────────────┐
│  Browser   │ ────────────────▶ │   FastAPI + SSE stream        │
│ (chat UI)  │ ◀──────────────── │   /api/chat/stream            │
└────────────┘  status/plan/msg  └──────────────┬───────────────┘
                                                ▼
                                   ┌────────────────────────────┐
                                   │  Agent loop (LLM + tools)  │
                                   │                            │
                                   │  ┌────────┐  ┌──────────┐  │
                                   │  │ search │  │  fetch   │  │
                                   │  │  web   │  │  page    │  │
                                   │  └────────┘  └──────────┘  │
                                   │  ┌────────┐  ┌──────────┐  │
                                   │  │knowledge│  │ ask_user │  │
                                   │  │  base   │  │ (pause)  │  │
                                   │  └────────┘  └──────────┘  │
                                   │  ┌──────────────────────┐  │
                                   │  │   generate_plan 🎯   │  │
                                   │  └──────────────────────┘  │
                                   └────────────────────────────┘
```

- **Curated knowledge base** (`data/visa_programs.json`) — Egypt-specific baseline (visa types, documents, fees, application routes) that the agent always cross-checks against **live web results**.
- **Streaming (SSE)** — you see live status ("Searching official sources…") instead of a spinner.
- **Resilience** — retries with varied temperature, per-turn research budget, and history compaction keep free-tier API quirks from breaking the demo.

---

## 🧰 Tech stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12 · **FastAPI** · Uvicorn |
| LLM | OpenAI-compatible SDK → **Groq free tier** (`openai/gpt-oss-120b`), any OpenAI-compatible endpoint works |
| Web search | **DuckDuckGo** (free, no key) or **Tavily** (optional) |
| Web scraping | `requests` + `BeautifulSoup` |
| Exchange rate | Frankfurter / open.er-api (free, ECB data) |
| Frontend | Vanilla HTML/CSS/JS (no build step), **English + Arabic (RTL)** |

---

## 📁 Repository structure

```
veezaAI/
├── app.py                 # Hugging Face Spaces / Docker entrypoint
├── requirements.txt       # Root deps (Docker / HF Spaces)
├── Dockerfile             # Docker / HF Spaces image
├── run.py                 # Local dev launcher (port 8000)
├── backend/
│   ├── app.py             # FastAPI app: SSE chat, rate, knowledge, static files
│   ├── agent.py           # Tool-calling agent loop (interview → plan)
│   ├── tools.py           # search_web, fetch_page, search_knowledge_base
│   ├── exchange.py        # Live EUR→EGP rate (cached)
│   └── config.py          # Settings from env / .env
├── data/
│   └── visa_programs.json # Curated Egypt-specific visa knowledge base
├── frontend/
│   ├── index.html         # Chat UI + plan panel
│   ├── style.css          # Styles, RTL + print/PDF styles
│   └── app.js             # SSE streaming, i18n, checklist, history, EGP
├── .env.example           # Copy to .env and fill in your key
└── LICENSE
```

---

## 🚀 Quickstart (local)

Requires **Python 3.12+** and a free **Groq API key** (<https://console.groq.com>).

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure your API key
cp .env.example .env      # Windows: Copy-Item .env.example .env
# then set LLM_API_KEY=<your key> in .env

# 3. Run
python run.py
```

Open **<http://127.0.0.1:8000>** and start chatting.

### With Docker

```bash
docker build -t veeza-ai .
docker run -p 7860:7860 -e LLM_API_KEY=<your key> veeza-ai
```

Open **<http://localhost:7860>**.

---

## ⚙️ Configuration

| Variable | Default | Notes |
|---|---|---|
| `LLM_API_KEY` | — | **Required.** Groq / OpenRouter / any OpenAI-compatible key |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | Override for OpenRouter etc. |
| `LLM_MODEL` | `openai/gpt-oss-120b` | Must support function calling |
| `TAVILY_API_KEY` | empty | Optional; enables Tavily search |

> **Model tips:** `openai/gpt-oss-120b` (default) is the most reliable free tool-calling model on Groq; `qwen/qwen3.6-27b` has excellent Arabic. Avoid `llama-3.3-70b-versatile` — its tool-call parsing is flaky and it drains the free daily token cap fast.

---

## 🔌 API

| Endpoint | Description |
|---|---|
| `POST /api/chat/stream` | SSE stream. Body: `{session_id?, message}` → events `{type: "status"\|"question"\|"message"\|"plan"}` |
| `POST /api/chat` | Non-streaming version. Returns `{session_id, reply, kind, plan}` |
| `POST /api/reset` | `{session_id}` → clears a conversation |
| `GET /api/rate` | `{eur_to_egp}` — live EUR→EGP rate |
| `GET /api/knowledge` | The curated knowledge base |
| `GET /api/health` | Health check |

`kind: "question"` means the agent is waiting for your answer; keep replying with the same `session_id`. `kind: "plan"` includes the full structured plan object.

---

## ☁️ Deployment

### GitHub

```bash
git init
git add .
git commit -m "Initial commit: AI visa assistant for Egyptians"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> 🔒 The `.gitignore` excludes `.env` — your API key never gets committed.

### Hugging Face Spaces

1. Create a **Docker** SDK Space at <https://huggingface.co/new-space> (name it e.g. `veeza-ai`).
2. Push the same repo to the Space:

```bash
git remote add space https://huggingface.co/spaces/<your-username>/veeza-ai
git push space main
```

3. In **Space Settings → Variables and secrets**, add the secret:
   - `LLM_API_KEY` = your Groq key

The `Dockerfile` already listens on port **7860** (HF's default). Your Space will be live at
`https://huggingface.co/spaces/<your-username>/veeza-ai`.

---

## 📜 License & disclaimer

[MIT](LICENSE).

This tool aggregates **public information** for research and planning only. It is **not legal advice** and does **not** guarantee visa approval. Fees, documents and procedures change frequently — always confirm on the official embassy / visa-centre website before paying or submitting anything.
