# Backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir hatch && \
    pip install --no-cache-dir fastapi uvicorn python-multipart pydantic pydantic-settings \
    sqlalchemy aiosqlite redis celery httpx aiohttp huggingface-hub python-jose passlib python-dotenv loguru Pillow

# Copy application
COPY backend/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
