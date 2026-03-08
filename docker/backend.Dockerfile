# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/app ./app

# Create data directory
RUN mkdir -p /data

EXPOSE 8080

ENV DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sudp
ENV DATA_STORAGE_PATH=/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]