# ==============================================================================
# ORAGAI - Dockerfile (Multi-stage Build for Development & Production)
# ==============================================================================

FROM python:3.13-slim AS base

# Prevent interactive prompts and configure uv environment
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /workspace/orchestrator-ai-agent

# Create a clean virtual environment in /opt/venv
RUN uv venv /opt/venv --python /usr/local/bin/python

# Step 1: Copy dependency specifications for Docker layer caching
COPY pyproject.toml uv.lock ./
COPY README.md ./README.md

# Step 2: Pre-install dependencies into /opt/venv (cached layer)
RUN uv sync --frozen --no-install-project

# Step 3: Copy full project codebase
COPY . .

# Step 4: Install the project itself (oragai) into /opt/venv
RUN uv sync --frozen

# ==============================================================================
# Stage: development (Supports both standalone and live-mounted workflows)
# ==============================================================================
FROM base AS development

CMD ["sleep", "infinity"]

# ==============================================================================
# Stage: production (Direct CLI entrypoint)
# ==============================================================================
FROM base AS production

ENTRYPOINT ["python", "-m", "orchestrator.main"]
CMD ["--check-config"]
