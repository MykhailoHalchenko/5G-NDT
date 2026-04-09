FROM python:3.11-slim

LABEL maintainer="KAI Network Lab" \
      description="5G Network Digital Twin API"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY setup.py .
COPY config/ ./config/

# Non-root user for security
RUN useradd -r -u 1001 -g root ndt && chown -R ndt:root /app
USER ndt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
