# Multi-stage Dockerfile for Algorithmic Consensus
# Stage 1: Build React frontend
# Stage 2: Python API server serving the built frontend

# --- Stage 1: Build frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python API ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY api/ ./api/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
