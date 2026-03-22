# Algorithmic Consensus - System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    main.py (CLI Interface)                   │
├──────────────┬──────────────────────┬───────────────────────┤
│  voice.py    │  deliberation.py     │  consensus.py         │
│  PILLAR 1    │  PILLAR 2            │  PILLAR 3             │
│  Input Layer │  Processing Layer    │  Output Layer         │
│              │                      │                       │
│  • Whisper   │  • Vote Matrix       │  • Unity Score        │
│    ASR       │  • PCA (2D)          │  • Consensus Index    │
│  • Text      │  • K-Means           │  • Fear Heatmap       │
│    Input     │    Clustering        │  • Report Generator   │
│  • Embedding │  • Bridge Statement  │                       │
│  • Sentiment │    Detection         │                       │
├──────────────┴──────────────────────┴───────────────────────┤
│                 models.py (Data Layer)                       │
│                 SQLite + Dataclasses                         │
├─────────────────────────────────────────────────────────────┤
│                 config.py (Configuration)                    │
└─────────────────────────────────────────────────────────────┘
```

### Web Architecture (added 2026-03-22)

```
┌─────────────────────────────────────────────────────────────┐
│              frontend/ (React + TypeScript + Vite)           │
│                                                             │
│  Participant UI              │  Analyst Dashboard           │
│  • ParticipantHome           │  • Dashboard                 │
│  • SubmitStatement           │    ├─ MetricCard (x4)        │
│    (text + audio recorder)   │    ├─ ClusterScatter         │
│  • VotingBooth               │    │  (Recharts scatter)     │
│    (card-by-card voting)     │    ├─ FearHeatmap            │
│  • MyProgress                │    │  (Nivo heatmap)         │
│    (vote history)            │    ├─ BridgeStatementList    │
│                              │    └─ ClusterSummary         │
├──────────────────────────────┴──────────────────────────────┤
│                    api/ (FastAPI REST Layer)                 │
│                                                             │
│  Thin wrapper -- zero business logic, only HTTP translation │
│                                                             │
│  POST /api/participants      → models.create_participant()  │
│  GET  /api/statements        → models.get_all_statements()  │
│  POST /api/statements        → InputProcessor + add_stmt()  │
│  POST /api/statements/audio  → Whisper ASR + add_stmt()     │
│  POST /api/votes             → models.cast_vote()           │
│  GET  /api/votes/next/{pid}  → models.get_next_unvoted()    │
│  GET  /api/votes/history     → models.get_participant_votes()│
│  GET  /api/status            → models.get_stats()           │
│  POST /api/analysis          → Engine + Analyzer pipeline   │
│  GET  /api/analysis/latest   → models.get_latest_result()   │
│  GET  /api/analysis/clusters → scatter data (JSON)          │
│  GET  /api/analysis/heatmap  → heatmap grid data (JSON)     │
├──────────────────────────────┴──────────────────────────────┤
│  Existing pillars: voice.py │ deliberation.py │ consensus.py│
├──────────────────────────────┴──────────────────────────────┤
│                 models.py (Data Layer)                       │
│                 SQLite + Dataclasses                         │
├─────────────────────────────────────────────────────────────┤
│                 config.py (Configuration)                    │
└─────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. Human speaks (voice) or types (text) a statement
2. voice.py transcribes (if voice), validates, computes embedding + sentiment
3. Statement stored in SQLite via models.py
4. Other participants vote agree/disagree/pass on each statement
5. deliberation.py builds vote matrix, runs PCA + clustering, finds bridge statements
6. consensus.py computes metrics and generates reports for policymakers

**Key principle: AI observes and measures; humans speak and decide.**
No generative AI produces content in the deliberation. The only AI models are:
- Whisper (speech-to-text transcription)
- sentence-transformers (semantic similarity embeddings)
- camel-tools (Arabic sentiment classification)

---

## Design Decisions Log

| Date | Decision | Rationale | Alternatives Rejected |
|------|----------|-----------|----------------------|
| 2026-03-22 | SQLite over PostgreSQL | Zero-config, stdlib, sufficient for prototype | PostgreSQL (overkill), MongoDB (schema-less risk) |
| 2026-03-22 | paraphrase-multilingual-mpnet-base-v2 | Best quality multilingual embeddings (768-dim), strong Arabic | MiniLM (384-dim, faster but lower quality) |
| 2026-03-22 | camel-tools for Arabic sentiment | Purpose-built for Arabic, MIT license, offline-capable | TextBlob (no Arabic), GPT API (cost + hallucination) |
| 2026-03-22 | 60% bridge threshold | Polis convention, reasonable for diverse groups | 50% (too permissive), 70% (too strict for small N) |
| 2026-03-22 | 140-char statement limit | Polis proven convention, forces concise ideas | No limit (invites essays, drowns out short voices) |
| 2026-03-22 | No direct replies | Polis design: kills trolling, forces constructive input | Threading (enables flame wars) |
| 2026-03-22 | Column-mean imputation | Same as Polis for missing votes, unbiased at scale | Zero imputation (conflates "didn't see" with "pass") |
| 2026-03-22 | Silhouette score for k selection | Objective, no manual tuning, well-understood metric | Elbow method (subjective), fixed k (arbitrary) |
| 2026-03-22 | Flat file structure (no subdirs) | 9 files total, minimal sprawl as requested | src/ package layout (unnecessary for prototype) |
| 2026-03-22 | Click for CLI | Clean decorator syntax, widely used, good help text | argparse (more verbose), Typer (extra dependency) |
| 2026-03-22 | FastAPI for web API | Modern async, auto-generates OpenAPI docs at /docs, minimal code | Flask (no auto docs), Django REST (overkill) |
| 2026-03-22 | React + TypeScript + Vite for frontend | Component-based, type-safe, fast HMR, good for interactive dashboards | Vue (less ecosystem), plain HTML/JS (no components) |
| 2026-03-22 | Arabic-only RTL via `dir="rtl"` + CSS logical properties | Single target audience, automatic layout flip, no i18n library needed | Bilingual with i18next (added complexity for prototype) |
| 2026-03-22 | IBM Plex Sans Arabic font | Free (Google Fonts), excellent Arabic rendering, all weights | Noto Sans Arabic (heavier), system fonts (inconsistent) |
| 2026-03-22 | React Query for state management | All state is server-state, built-in caching/refetch/mutations | Redux (overkill), Context (no caching intelligence) |
| 2026-03-22 | Recharts + @nivo/heatmap for charts | React-native components, good Arabic text handling | D3 directly (too imperative), Chart.js (less composable) |
| 2026-03-22 | MediaRecorder API for audio capture | Native browser API, no library needed, webm/opus output | RecordRTC (extra dependency), Web Audio API (lower-level) |
| 2026-03-22 | Vite proxy in dev, FastAPI static mount in prod | One port in production, hot reload in dev, zero CORS issues | Separate servers (CORS complexity), nginx (extra infra) |
| 2026-03-22 | `check_same_thread=False` for SQLite in FastAPI | FastAPI runs sync handlers in threadpool; connections cross threads | Single-thread executor (serializes all requests), aiosqlite (rewrites all queries) |
| 2026-03-22 | Analysis endpoints create own connections | Heavy analysis runs in threadpool workers; injected conn can't cross threads | `run_in_executor` with injected conn (crashes), async rewrite of analysis (too invasive) |

---

## Algorithm Reference

### PCA + K-Means Pipeline (deliberation.py)

```
Vote Matrix M (P participants × S statements):
    M[i][j] = 1 (agree), -1 (disagree), 0 (pass), NaN (unvoted)

Step 1: Impute NaN with column means
Step 2: PCA → project to 2D (captures max variance in voting patterns)
Step 3: K-Means on 2D projections, k chosen by best silhouette score (k=2..5)
Step 4: For each statement, compute agreement rate per cluster
Step 5: If statement has ≥60% agreement in ≥2 clusters → BRIDGE STATEMENT
```

### Bridge Score Formula

```
For statement j, cluster c:
    agreement_rate(j, c) = count(votes == 1 from cluster c) / total_votes_from_cluster_c

bridge_score(j) = mean(agreement_rate(j, c) for all c where agreement_rate ≥ 0.60)
clusters_agreeing(j) = count of clusters where agreement_rate ≥ 0.60

Statement j is a bridge if clusters_agreeing(j) ≥ 2
```

### Consensus Metrics

```
Unity Score = num_bridge_statements / total_statements
    Range: 0.0 (total polarization) to 1.0 (full consensus)
    Healthy: 0.15 - 0.40

Consensus Index = Σ(weight_b × score_b) / Σ(weight_b) for all bridges b
    where weight_b = clusters_agreeing_b / total_clusters
    and score_b = bridge_score_b
    Range: 0.0 to 1.0
```

---

## Change Tracking

### 2026-03-22 - Initial Build

**Phase 1: Foundation**
- Created `config.py` with all tunable parameters
- Created `models.py` with SQLite schema, CRUD operations, vote matrix builder, seed data
- Created `requirements.txt` with 8 dependencies
- Created `DESIGN.md` (this file)

**Key decisions made:**
- Flat file structure (9 files, no subdirectories) to minimize sprawl
- All parameters centralized in config.py
- UUID-based anonymous IDs for privacy
- Vote matrix uses NaN for unvoted (not zero) to distinguish from "pass"
- Seed data creates 3 distinct opinion groups for testing cluster detection

### 2026-03-22 - Web Frontend + API Layer

**Phase 2: FastAPI Backend (`api/`)**
- Created `api/app.py` - FastAPI application factory with CORS, lifespan, router wiring, static file mount
- Created `api/deps.py` - Dependency injection: per-request SQLite connections (`check_same_thread=False`), InputProcessor singleton via lifespan
- Created `api/schemas.py` - 14 Pydantic request/response models translating between JSON and existing dataclasses
- Created 5 routers (`participants.py`, `statements.py`, `votes.py`, `status.py`, `analysis.py`) - 15 total endpoints
- Added 3 helper queries to `models.py`: `get_next_unvoted_statement()`, `get_participant_votes()`, `get_latest_result()`
- Added `fastapi`, `uvicorn[standard]`, `python-multipart` to `requirements.txt`

**Phase 3: React Frontend (`frontend/`)**
- Scaffolded with Vite + React + TypeScript
- Arabic-only RTL interface: `<html dir="rtl" lang="ar">`, IBM Plex Sans Arabic font, CSS logical properties
- 5 pages: ParticipantHome, SubmitStatement, VotingBooth, MyProgress, Dashboard
- 9 components: Navbar, StatementCard, VoteButtons, AudioRecorder, MetricCard, ClusterScatter, FearHeatmap, BridgeStatementList, ClusterSummary
- API layer: Axios client + 13 React Query hooks for all endpoints
- Vite proxy config: `/api` requests forwarded to FastAPI (port 8000) in dev mode

**Bugs fixed:**
- SQLite `ProgrammingError: objects created in a thread can only be used in that same thread` - FastAPI dispatches sync handlers to a threadpool, so connections cross thread boundaries. Fixed by using `check_same_thread=False` in `deps.py` and having analysis endpoints create their own connections via `_make_conn()` instead of using the injected dependency
- Missing `pyrsistent` module for `camel-tools` sentiment analysis - installed as runtime dependency
- `config.py` `SENTIMENT_MODEL` was set to HuggingFace-style name `CAMeL-Lab/bert-base-arabic-camelbert-da-sentiment` but camel-tools expects the catalogue short name `arabert`. Fixed config to use `arabert`
- camel-tools arabert model data not downloaded - ran `camel_data -i sentiment-analysis-arabert` to download the ~541MB model to local cache (`AppData/Roaming/camel_tools/data/sentiment_analysis/arabert`)

**Key architectural decisions:**
- API layer is a thin wrapper with zero business logic; all existing Python modules imported as-is
- CLI (`python main.py ...`) continues to work unchanged alongside the web interface
- Analysis endpoints (`POST /analysis`, `GET /analysis/clusters`, `GET /analysis/heatmap`) create their own DB connections rather than using FastAPI dependency injection, because `DeliberationEngine` and `ConsensusAnalyzer` run CPU-heavy work across threadpool boundaries
- Frontend stores only `participantId` in `localStorage`; all other state is server-state managed by React Query
- Dark theme with Arabic-optimized typography and RTL-first layout

### 2026-03-22 - Frontend Polish + Deployment Config

**UI/UX Improvements:**
- Added Toast notification system (`Toast.tsx`) with slide-in/out animations for success/error/info feedback on all mutations
- Added Skeleton loading components (`Skeleton.tsx`) with shimmer animation for all loading states (status cards, metric cards, vote cards, dashboard charts)
- Added `fade-in` CSS animation class applied to all page containers for smooth entry
- Added `stagger-children` CSS class for sequential card reveal animations (status cards, metric cards, vote history)
- Improved StatementCard: thicker right accent border, better line-height for Arabic text
- Improved MetricCard: top accent line in metric color, better spacing
- Improved VoteButtons: larger 56px min-height touch targets, 12px border-radius
- Better empty states for MyProgress (with CTA to vote) and Dashboard (with icon circle)
- Gradient progress bar (blue-to-purple) with fill animation

**Error Handling:**
- All mutation hooks now show toast on error
- Join, Submit, Vote, Run Analysis all provide user-visible feedback
- Audio endpoint returns 503 with clear message when ML models unavailable
- Text submission works in "lite mode" when processor is None (stores raw text, defaults sentiment to neutral)
- Error + retry states added to VotingBooth and MyProgress pages

**Mobile Responsive:**
- CSS hamburger menu icon visible below 640px, hides desktop nav links
- Mobile nav dropdown (`.nav-links.open`) with fixed positioning
- Touch-optimized: disabled hover transforms on touch devices, scale-down on active
- Flex-wrap on all card grids (status, metrics, action buttons, chart row)
- Charts and dashboard stack vertically on narrow screens

**Real-time Updates:**
- `useStatus()` polls every 8s (was 10s)
- `useStatements()` polls every 15s
- `useVoteHistory()` polls every 20s
- New statement submissions invalidate next-statement cache immediately
- `refetchOnWindowFocus: true` enabled globally
- `staleTime: 10s` (was 15s) with retry=2

**Deployment:**
- Created `Dockerfile` (multi-stage: Node 20 builds frontend, Python 3.11-slim serves API + static)
- Created `render.yaml` Blueprint for one-click Render deployment
- Created `.gitignore` covering Python, Node, SQLite, output, temp files
- Made InputProcessor loading graceful (try/catch in lifespan) - app starts in "lite mode" if ML packages fail to load
- CORS opened to allow_origins=["*"] for deployment
- Health check endpoint: `GET /api/status`

