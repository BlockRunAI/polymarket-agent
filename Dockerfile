# Polymarket AI Agent - Cloud Run Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create templates directory if needed
RUN mkdir -p templates

# Environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run with gunicorn for production
RUN pip install gunicorn

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 0 app:app
