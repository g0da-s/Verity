# TruthCheck Backend

Evidence-based health claim verification system using LangGraph and Claude Sonnet 4.5.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the server:
```bash
uv run uvicorn app.main:app --reload
```
