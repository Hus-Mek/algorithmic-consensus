"""
config.py - Central configuration for Algorithmic Consensus

Every tunable parameter lives here. If a number, path, or model name
appears in algorithm logic, it should be a named constant in this file.
"""

import os
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent
# Use DATA_DIR env var for persistent storage (e.g. Railway volume), fallback to project root
_data_dir = Path(os.environ.get("DATA_DIR", str(PROJECT_ROOT)))
DB_PATH = _data_dir / "consensus.db"
OUTPUT_DIR = _data_dir / "output"

# --- Voice / Input ---
WHISPER_MODEL_SIZE = "base"          # tiny|base|small|medium|large
WHISPER_LANGUAGE = "ar"              # Force Arabic recognition
MAX_STATEMENT_LENGTH = 140           # Polis-style character limit
INPUT_MODE = "text"                  # "voice" or "text" (togglable at runtime)

# --- Embeddings ---
# paraphrase-multilingual-mpnet-base-v2: 768-dim, strong Arabic support,
# highest-download multilingual model on HuggingFace (6M+ downloads).
# Alternative: MiniLM (384-dim, faster but lower quality for Arabic nuance)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIM = 768

# --- Deliberation ---
MIN_CLUSTERS = 2
MAX_CLUSTERS = 5                     # Cap for prototype (prevents over-segmentation)
BRIDGE_THRESHOLD = 0.60              # 60% agreement from 2+ clusters = bridge statement
MIN_VOTES_PER_STATEMENT = 3          # Minimum votes before statement enters analysis
MIN_PARTICIPANTS_FOR_ANALYSIS = 10   # Minimum participants for meaningful clustering
PCA_COMPONENTS = 2                   # 2D projection for visualization + clustering

# --- Sentiment ---
# camel-tools arabert: purpose-built for Arabic, MIT license.
# Alternative: TextBlob (no Arabic), GPT API (cost + hallucination risk)
SENTIMENT_MODEL = "arabert"

# --- Consensus Metrics ---
FEAR_SENTIMENT_LABEL = "negative"    # Sentiment label indicating fear/concern

# --- Privacy ---
ANON_ID_PREFIX = "participant_"      # Anonymous ID format prefix
