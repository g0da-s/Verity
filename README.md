# Verity — Evidence-Based Health Claim Verification

An AI-powered application that verifies health claims using scientific evidence from PubMed. A 3-agent LangGraph pipeline searches for studies, scores their quality, and synthesizes an evidence-based verdict.

## How It Works

A claim like *"Does creatine improve muscle strength?"* flows through three agents:

1. **Search Agent** — generates 2–3 optimized PubMed queries using Groq Llama, runs them in parallel, and deduplicates the results (~12–18 unique studies).
2. **Quality Evaluator** — scores every study 0–10 in a single LLM call based on study type, sample size, journal quality, and recency. Picks the top 5.
3. **Synthesis Agent** — reads the top studies and produces a verdict (Strongly Supported → Contradicted) with a structured summary: bottom line, key findings, who benefits most, dosage/timing (if reported), and caveats. Grounding rules prevent the LLM from inventing facts not present in the abstracts.

Results are cached in SQLite for 30 days. Repeated claims skip the pipeline entirely.

## Architecture

```
frontend/          Next.js 16 + React 19 + Tailwind CSS
backend/
  app/
    agents/        search_agent · quality_evaluator · synthesis_agent
    api/routes/    verity.py  (POST /api/verity/verify)
    models/        state.py (LangGraph state) · database.py (SQLAlchemy)
    services/      cache.py · claim_validator.py
    tools/         pubmed.py  (Biopython Entrez wrapper)
    utils/         retry.py · normalize.py · rate_limit.py
    db/            session.py · init_db.py
    graph.py       LangGraph workflow definition
    config.py      Pydantic settings from .env
    main.py        FastAPI app + startup
```

## Setup

**Prerequisites:** Python 3.12+, Node.js 18+, a [Groq API key](https://console.groq.com), and a PubMed email address (free, required by NCBI).

### Backend

```bash
cd backend
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv sync

cp .env.example .env
# Edit .env — set GROQ_API_KEY and PUBMED_EMAIL at minimum

uv run python app/db/init_db.py        # create SQLite tables
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                            # http://localhost:3000
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (used by all three agents) |
| `PUBMED_EMAIL` | yes | Email for NCBI E-utilities rate-limit tier |
| `LANGSMITH_API_KEY` | no | Enables LangSmith tracing |
| `DATABASE_URL` | no | Defaults to `sqlite+aiosqlite:///./data/verity.db` |

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12, FastAPI, LangGraph, Groq Llama 3.3 70B |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Data | SQLite + SQLAlchemy (async), Biopython (PubMed) |
| Observability | LangSmith (optional) |

## Testing

```bash
cd backend
uv run pytest tests/
```

---

Built by Goda Smulk for Turing College.
