# 🐳 ORAGAI Docker Operations & Rebuild Guide

> Comprehensive guide for running, developing, testing, and understanding image rebuilding in Docker with ORAGAI.

---

## ⚡ Quick Answer: "Do I need to rebuild on every update?"

| What You Changed | Do You Need to Rebuild (`docker build`)? | How to Run / Apply |
| :--- | :---: | :--- |
| **`.env` File** (API keys, models, configs) | ❌ **No** | Injected dynamically at runtime via `--env-file .env`. |
| **Configuration Files** (`.json`, `.yaml`) | ❌ **No** (with `-v` mount) / ⚠️ **Fast Rebuild (~1s)** (without mount) | Applied automatically when mounted or in 1s build. |
| **Python Code** (`.py` files in `orchestrator/`) | ❌ **No** (with `-v` mount) / ⚠️ **Fast Rebuild (~1s)** (without mount) | Edits apply instantly when using directory mounts (`-v`). |
| **Dependencies** (`pyproject.toml`, `uv.lock`) | ✅ **Yes** | Rebuild required so `uv sync` installs the new packages. |
| **System Tools / Base OS** (`Dockerfile`) | ✅ **Yes** | Rebuild required to install new system binaries. |

---

## 🏗️ The 2 Development Modes

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      MODE A: LIVE BIND MOUNT (ZERO REBUILDS)                            │
│  - Mount your host source directory directly into `/workspace/orchestrator-ai-agent`     │
│  - Any edit to Python code, configs, or tests takes effect INSTANTLY without rebuilds.  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      MODE B: IMMUTABLE IMAGE (FAST REBUILDS)                            │
│  - Source code is baked directly into the Docker image layer.                           │
│  - Runs uniformly on remote servers or VMs over SSH context (`debian-vm`).              │
│  - Thanks to `uv` package caching, rebuilding takes only ~1 to 2 seconds.               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Execution Commands Reference

### 1. Fast Rebuild Command (1–2 Seconds)
When you want to update the baked image:
```powershell
docker build --target development -t oragai:dev . ; docker image prune -f
```

### 2. Check System Configuration & API Keys
Verify your environment and model access offline:
```powershell
docker run --rm --env-file .env oragai:dev python -m orchestrator.main --check-config
```

### 3. List Discovered Agent Skills
Inspect all active skills categorized by persona role:
```powershell
docker run --rm oragai:dev python -m orchestrator.main --list-skills
```

### 4. Run Codebase Audit (Zero Code Mutation)
Perform deep inspection and detect architectural drift:
```powershell
docker run --rm oragai:dev python -m orchestrator.main --mode audit
```

### 5. Execute an Autonomous Engineering Task
Run the 4-agent pipeline (Architect, Developer, Tester, Reviewer):
```powershell
docker run --rm -it --env-file .env oragai:dev python -m orchestrator.main "Build a REST endpoint for health checks" --mode dev-test
```

### 6. Pre-Execution Cost & Token Estimation
Estimate token consumption and budget before running LLMs:
```powershell
docker run --rm oragai:dev python -m orchestrator.main "Refactor authentication flow" --estimate
```

### 7. Run Full Automated Test Suite (~458 Test Functions)
Run pytest inside the hermetic Linux container:
```powershell
docker run --rm --entrypoint pytest oragai:dev tests/ -v
```

---

## 📦 Docker Compose Workflow (Optional)

If you prefer `docker compose`:

```powershell
# Check config
docker compose run --rm cli --check-config

# Run task
docker compose run --rm cli "Task description" --mode dev-test

# Run tests
docker compose run --rm test
```

---

## 🧹 Maintenance & Cleanup

To clean dangling image layers created during iterative builds:
```powershell
docker image prune --filter "dangling=true" -f
```
