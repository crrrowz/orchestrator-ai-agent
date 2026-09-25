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

# Production Containerization

## 1. Dockerfile Standards
- Multi-stage builds: isolate build tooling from minimal runtime image (`python:3.12-slim`).
- Non-root user: define unprivileged user (`USER appuser`).
- Layer caching: copy dependency definitions (`pyproject.toml`) and install prior to copying source.
- Healthchecks: include explicit `HEALTHCHECK` instructions.

## 2. Compose & Runtime Standards
- Use named volumes for persistent state and set restart policies (`restart: unless-stopped`).
- Enforce CPU and memory resource bounds.
- Inject secrets via `.env` rather than baking keys into images.
