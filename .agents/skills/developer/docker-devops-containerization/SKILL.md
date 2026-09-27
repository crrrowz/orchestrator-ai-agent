---
name: docker-devops-containerization
description: End-to-end Dockerization and developer environment protocol. Analyzes codebases (Python, Node.js, Polyglot), generates hermetic multi-stage Dockerfiles (dev & prod targets), docker-compose.yml with volume isolation, optimized .dockerignore, .devcontainer configs, and comprehensive dual-architecture DOCKER_GUIDE.md (Local Docker Desktop vs Remote VM via SSH context, dangling=true cleanup).
triggers:
  - docker
  - container
  - devops
  - dockerfile
  - compose
  - docker-compose
  - devcontainer
  - docker-guide
  - dangling-images
---

# End-to-End Docker Workspace Engineering & Operational Protocol

## 1. DUAL-ARCHITECTURE STRATEGY

Always configure projects to support both Docker operational models:

### Architecture 1: Local Docker Engine (Docker Desktop or Native Linux)
* Host filesystem and Docker Engine share the same disk.
* Live Bind Mount (`-v ${PWD}:/workspace/...` or `docker compose`) allows instant code reflections with **zero rebuilds**.

### Architecture 2: Remote Docker Engine (Debian VM via SSH Context)
* Developer edits on Windows; Docker commands run on remote VM via SSH.
* Cross-machine bind mounts do not work directly without network shared folders.
* Standard workflow: `docker build` (1–2s via `uv` package caching) + auto-cleaning dangling images (`docker image prune -f`).

---

## 2. THE FIVE REQUIRED DOCKER ARTIFACTS

Every project containerization must produce:

1. **`.dockerignore`**: Exclude host `.venv`, `node_modules`, `.git`, bytecode caches, and `.env` secrets.
2. **`Dockerfile`**: Multi-stage build with `base`, `development` (pre-cached deps, sleep infinity), and `production` (bundled code, immutable CLI entrypoint).
3. **`docker-compose.yml`**: Provides `dev`, `cli`, and `test` services with volume isolation for virtual environments (`venv-isolation`).
4. **`.devcontainer/devcontainer.json`**: Configures IDE interpreter paths, settings, and `postCreateCommand: uv sync`.
5. **`docs/DOCKER_GUIDE.md`**: Complete operational manual detailing the two architectures, rebuild decision matrix, cheat sheet, context switching, and dangling image cleanup.

---

## 3. REBUILD DECISION MATRIX

| Change Type | Architecture 1 (Local Engine) | Architecture 2 (Remote Debian VM) | Explanation |
| :--- | :---: | :---: | :--- |
| **`.env` File** (API keys, models, configs) | ❌ **Never** | ❌ **Never** | Injected dynamically at runtime via `--env-file .env`. Never baked into image layers. |
| **Python Code** (`.py` files) | ❌ **No Rebuild** (Live `-v` Mount) | ⚠️ **Quick Rebuild** (~1–2s) | Instant with live mount; requires quick `docker build` on remote VM (unless shared folder is used). |
| **Dependencies** (`pyproject.toml` / `uv.lock`) | ✅ **Yes** | ✅ **Yes** | Required so `uv sync` downloads and updates packages inside `/opt/venv`. |
| **System Tools / Base Image** (`Dockerfile`) | ✅ **Yes** | ✅ **Yes** | Required to apply changes to OS packages, build tools, or base configuration. |

---

## 4. DANGLING IMAGE MANAGEMENT (`dangling=true`)

When rebuilding images repeatedly, old layers become untagged (`<none>:<none>`). Always clean them:
* List: `docker images -f "dangling=true"`
* Prune: `docker image prune --filter "dangling=true" -f`
* Recommended one-liner: `docker build --target development -t <image>:dev . ; docker image prune -f`
