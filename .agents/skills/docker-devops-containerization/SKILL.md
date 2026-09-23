---
name: docker-devops-containerization
description: Production containerization and DevOps protocol. Enforces multi-stage builds, non-root users, minimal image footprints, and docker-compose orchestration.
triggers:
  - docker
  - container
  - devops
  - dockerfile
  - compose
---

# Production Docker & Containerization Protocol

## 1. Dockerfile Best Practices
- **Multi-Stage Builds**: Separate build dependencies (compilers, build-essential) from runtime artifacts to produce tiny, secure production images.
- **Minimal Base Images**: Prefer `python:3.12-slim` or `alpine` over bloated full OS images.
- **Least Privilege (Non-Root User)**: Always create and switch to an unprivileged user before the entrypoint:
  ```dockerfile
  RUN useradd -m -u 1000 appuser
  USER appuser
  ```
- **Layer Caching**: Copy dependency files (`pyproject.toml`, `requirements.txt`) and install packages before copying the full source tree.
- **Explicit Health Checks**: Always define a `HEALTHCHECK` instruction to enable orchestrator monitoring.

## 2. Docker Compose Standards
- Always declare named volumes for persistent data.
- Explicitly configure container restart policies (`restart: unless-stopped`).
- Set CPU and memory resource limits in compose configurations.
- Use `.env` files for configuration injection rather than baking secrets into images.
