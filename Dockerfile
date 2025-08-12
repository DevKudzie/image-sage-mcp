# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, kept minimal)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy project and install
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Default command: run MCP server over stdio
ENTRYPOINT ["image-sage-mcp"]

