# mcp/Dockerfile
# ------------------------------------------------------------------------------
# Base Dockerfile for MCP servers (ClickHouse + Postgres)
# This image contains all required dependencies and source code.
# Individual services will override the CMD via docker-compose.
# ------------------------------------------------------------------------------

# 1. Base Image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# 2. Install System-Level Dependencies
# Includes essential build tools and Postgres dependencies (libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    \
    # Add additional system dependencies here if your tools require them.
    # Example: OCR, PDF processing, image processing libraries
    # tesseract-ocr \
    # libpoppler-dev \
    # libgl1-mesa-glx \
    \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Python Packages
# Requirements should include both MCP server dependencies and tool-function packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4. Copy Source Code
# Ensure code structure is preserved inside the container
COPY src /app/src
COPY utils /app/utils
COPY variables /app/variables
COPY plugins /app/plugins


# 5. Expose Default MCP Server Ports
# ClickHouse MCP: 8080
# Postgres MCP: 8081
EXPOSE 8080
EXPOSE 8081
EXPOSE 8082

# 6. Default Startup Command
# This will be overridden per-service in docker-compose
CMD ["python", "-m", "src.mcp_server.clickhouse_server"]
