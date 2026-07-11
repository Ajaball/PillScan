FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render provides the port via the $PORT env var (defaults to 8001 locally).
ENV PORT=8001
EXPOSE 8001

CMD ["sh", "-c", "uvicorn inference.server:app --host 0.0.0.0 --port ${PORT:-8001}"]
