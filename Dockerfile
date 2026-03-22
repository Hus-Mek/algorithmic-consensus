# Multi-stage Dockerfile for Algorithmic Consensus
# Stage 1: Build React frontend
# Stage 2: Python API server serving the built frontend (lite mode - no ML)

# --- Stage 1: Build frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python API (lite mode) ---
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies (lite - no ML models)
COPY requirements-lite.txt ./
RUN pip install --no-cache-dir -r requirements-lite.txt

# Copy application code
COPY *.py ./
COPY api/ ./api/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Railway uses PORT env var
CMD uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}
