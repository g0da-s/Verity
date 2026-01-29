# 🔬 TruthCheck - Evidence-Based Health Claim Verification

An AI-powered application that verifies health claims using scientific evidence from PubMed, powered by Claude Sonnet 4.5 and LangGraph.

## 🎯 Features

- **3-Agent Pipeline**: Search → Quality Evaluation → Synthesis
- **PubMed Integration**: Searches 36M+ scientific articles
- **Smart Quality Scoring**: Evaluates studies on methodology, sample size, and recency
- **Evidence-Based Verdicts**: Generates nuanced conclusions with citations
- **Modern UI**: Clean, playful interface with real-time progress tracking

## 🏗️ Architecture

### Backend (Python)
- **Framework**: FastAPI + LangGraph
- **AI Model**: Claude Sonnet 4.5 (Anthropic)
- **Database**: SQLite with SQLAlchemy
- **APIs**: PubMed E-utilities (Biopython)

### Frontend (TypeScript)
- **Framework**: Next.js 16 + React
- **Styling**: Tailwind CSS
- **UI**: Green/nature theme, card-based design

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Anthropic API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Add your API keys to .env:
# - ANTHROPIC_API_KEY
# - PUBMED_EMAIL
# - LANGSMITH_API_KEY (optional)

# Initialize database
uv run python app/db/init_db.py

# Start API server
uv run uvicorn app.main:app --reload
# API runs on http://localhost:8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

### 3. Test the Application

Open http://localhost:3000 in your browser and try example claims:
- "Does creatine improve muscle strength?"
- "Does vitamin C prevent colds?"
- "Is intermittent fasting effective for weight loss?"

## 📖 How It Works

### Agent Pipeline

1. **🔍 Search Agent**
   - Uses Claude to generate 3 optimized PubMed queries
   - Searches for meta-analyses, RCTs, and systematic reviews
   - Returns ~12 unique studies (6 per query)

2. **⚖️ Quality Evaluator**
   - Scores each study (0-10) based on:
     - Study type (meta-analysis > RCT > observational)
     - Sample size (larger = better)
     - Journal quality
     - Recency (newer = better)
   - Selects top 5 highest-quality studies

3. **✍️ Synthesis Agent**
   - Analyzes findings from top studies
   - Generates evidence-based verdict
   - Creates summary with citations

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Test full pipeline
uv run python tests/test_full_pipeline.py

# Test LangGraph workflow
uv run python tests/test_langgraph.py
```

## 📊 Performance

- **Pipeline Time**: 30-60 seconds per claim
- **Studies Analyzed**: 12 studies → Top 5 selected

## 🛠️ Tech Stack

- FastAPI, LangGraph, Claude Sonnet 4.5
- Next.js 16, React, TypeScript, Tailwind
- PubMed API, SQLite

---

Built by Goda Smulk for Turing College
