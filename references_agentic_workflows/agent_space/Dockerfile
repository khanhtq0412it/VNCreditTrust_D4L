# Multi-purpose Dockerfile for the agentspace Python project
# - Installs dependencies from requirements.txt (if present)
# - Adds a non-root user
# - Uses uvicorn to run the included langgraph server by default

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system deps commonly needed to build Python packages and curl for healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer cache
COPY requirements.txt ./

# Install Python dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then \
      python -m pip install --upgrade pip setuptools wheel && \
      pip install -r requirements.txt --no-cache-dir; \
    else \
      echo "requirements.txt not found, skipping pip install"; \
    fi

# Copy project files
COPY . /app

# Create an unprivileged user and set ownership
RUN groupadd --system app && useradd --system --gid app --home-dir /app --create-home app \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Healthcheck uses the server's agents listing endpoint (adjust if you have a different health path)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/agents || exit 1

# Default command: run the bundled light-weight LangGraph FastAPI server
CMD ["uvicorn", "framework.langgraph_server.server:app", "--host", "0.0.0.0", "--port", "8000"]
