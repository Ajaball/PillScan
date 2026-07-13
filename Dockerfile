# ── Root Dockerfile — builds the FastAPI backend from the repo-root context ──
# Render's *manually-created* Docker web services look for a Dockerfile at the
# repository root by default. Since the real backend Dockerfile lives in
# ./backend, a root-context build fails with:
#   "failed to read dockerfile: open Dockerfile: no such file or directory"
# This root file makes that "just work" WITHOUT having to set a Root Directory.
#
# Note: the render.yaml Blueprint still builds the backend via
# ./backend/Dockerfile with ./backend as the context, so it does NOT use this
# file. This is only used when Render builds from the repository root.
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (from the backend/ folder)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code into the image root
COPY backend/ .

# Create upload directories
RUN mkdir -p uploads/scans

# Render provides the port via the $PORT env var (defaults to 8000 locally).
ENV PORT=8000
EXPOSE 8000

# Run the application (production: no --reload, bind to $PORT from the host)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
