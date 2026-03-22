# Algorithmic Consensus

AI-driven deliberative framework for post-conflict peacebuilding, inspired by [vTaiwan](https://info.vtaiwan.tw/) and [Polis](https://pol.is/).

## What is this?

A platform where communities can build consensus through anonymous, card-by-card voting -- without direct replies or flame wars. AI observes and measures; humans speak and decide.

**Key principles:**
- **Voice-first**: Whisper ASR supports Syrian Arabic dialects for illiterate or displaced participants
- **Privacy-by-design**: UUID-based anonymous IDs, no names or GPS
- **Anti-hallucination**: AI never generates deliberation content -- only transcribes, embeds, and measures sentiment
- **Bridge detection**: Finds statements that achieve >60% agreement across opposing opinion clusters

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  React Frontend (Arabic RTL, dark theme)             │
│  Vite + TypeScript + React Query + Recharts          │
├──────────────────────────────────────────────────────┤
│  FastAPI API Layer (15 endpoints, zero business logic)│
├──────────┬───────────────────┬───────────────────────┤
│ voice.py │ deliberation.py   │ consensus.py          │
│ Input    │ Processing        │ Output                │
│ Whisper  │ PCA + K-Means     │ Unity Score           │
│ Embed    │ Bridge Detection  │ Consensus Index       │
│ Sentiment│                   │ Fear Heatmap          │
├──────────┴───────────────────┴───────────────────────┤
│  models.py (SQLite + dataclasses)                    │
│  config.py (all tunable parameters)                  │
└──────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend
```bash
pip install -r requirements.txt
camel_data -i sentiment-analysis-arabert   # ~541MB, needed for Arabic sentiment
uvicorn api.app:app --reload --port 8000
```

### Frontend (development)
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` requests to the backend at `localhost:8000`.

### Production
```bash
cd frontend && npm run build && cd ..
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

FastAPI auto-serves the built frontend from `frontend/dist/`.

### Docker
```bash
docker build -t algorithmic-consensus .
docker run -p 8000:8000 algorithmic-consensus
```

## Features

### For Participants
- **Join anonymously** -- no registration, just a UUID
- **Submit opinions** via text (140 chars) or voice recording
- **Vote card-by-card** -- agree, disagree, or pass on each statement
- **Track progress** -- see your voting history

### For Analysts
- **Unity Score** -- 0.0 (total polarization) to 1.0 (full consensus)
- **Consensus Index** -- weighted bridge statement metric
- **Cluster visualization** -- PCA scatter plot of opinion groups
- **Fear heatmap** -- geographic fear intensity by cluster
- **Bridge statements** -- ideas that unite opposing groups

## CLI Usage

The original CLI still works alongside the web interface:

```bash
python main.py add-participant --location "Damascus"
python main.py add-statement --author <UUID> --text "نحتاج إلى حكم محلي أقوى"
python main.py vote --participant <UUID> --statement 1 --value 1
python main.py run-analysis
python main.py show-results
```

## Lite Mode

If ML dependencies (Whisper, sentence-transformers, camel-tools) fail to load, the app starts in **lite mode**: text submission and voting work, but audio transcription and AI-powered analysis are disabled.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, React Query, Recharts, Framer Motion |
| API | FastAPI, Pydantic, uvicorn |
| ML | OpenAI Whisper, sentence-transformers, camel-tools (arabert) |
| Analysis | scikit-learn (PCA, K-Means), numpy, matplotlib |
| Database | SQLite with WAL mode |
| Language | Arabic RTL, IBM Plex Sans Arabic |

## License

MIT
