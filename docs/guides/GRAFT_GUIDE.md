# 🌿 ORAGAI Graft Codebase Intelligence & Wiring Guide

> Comprehensive operational and architectural guide for installing, configuring, and leveraging Graft CLI within ORAGAI for zero-token codebase orientation and structural navigation.

---

## ⚡ What is Graft?

**Graft** is a high-performance codebase intelligence and static wiring graph engine. Within ORAGAI, it provides **Zero-Token Codebase Discovery**:
- Maps project directory clusters and structural hotspots without loading whole files.
- Extracts interface signatures (skeletons) to inspect APIs with minimal token overhead.
- Analyzes call graphs and blast radiuses to verify the impact of modifications before editing.

---

## 🏗️ How ORAGAI Uses Graft

ORAGAI integrates Graft via `orchestrator/analysis/graft_context.py` and `GraftContextProvider`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AGENT INITIATION PHASE                          │
│        (Architect, Developer, Auditor Prompt Synthesis)                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                     Is `graft` or `graft.ps1` in PATH?
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼ YES                               ▼ NO
┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│     GraftContextProvider          │   │      Graceful Fallback Mode       │
│  - Builds graph index (`build`)   │   │  - Disables Graft prompt block    │
│  - Generates compact map (1500 ch)│   │  - Uses AST parser / file scans   │
│  - Injects into agent prompts     │   │  - Zero system crashes / errors   │
└───────────────────────────────────┘   └───────────────────────────────────┘
```

---

## 🚀 Installation & Setup

### 1. Verification
Check if Graft is already available on your machine:
```powershell
Get-Command graft* -ErrorAction SilentlyContinue
```
Or in CMD / Git Bash:
```bash
which graft || where graft
```

### 2. Windows PowerShell Setup
If you have the `graft.ps1` script, ensure its directory is added to your user or system `PATH`:
```powershell
# Temporarily add to current session
$env:Path += ";C:\path\to\graft\bin"

# Or permanently in PowerShell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User) + ";C:\path\to\graft\bin",
    [EnvironmentVariableTarget]::User
)
```

### 3. Docker Environment
To run Graft inside Docker, include the Graft binary or script in your multi-stage `Dockerfile`:
```dockerfile
# Copy graft binary or script to /usr/local/bin
COPY --from=graft-source /bin/graft /usr/local/bin/graft
RUN chmod +x /usr/local/bin/graft
```

---

## 🛠️ Core Commands Reference

| Operation | Command | Purpose in ORAGAI | Token Impact |
| :--- | :--- | :--- | :--- |
| **Graph Build** | `graft build` | Pre-computes code graph in `graft/` directory. | **0 tokens** |
| **Codebase Map** | `graft map` | Visualizes directory clusters, hubs, and hotspots. | **0 tokens** |
| **API Skeletons** | `graft skeleton <file>` | Extracts class/function signatures without bodies. | **>90% reduction** |
| **Inbound Callers**| `graft callers <symbol>` | Lists all functions/methods calling `<symbol>`. | **0 tokens** |
| **Outbound Deps** | `graft callers --direction out <symbol>` | Lists dependencies called by `<symbol>`. | **0 tokens** |
| **Blast Radius** | `graft blast` | Evaluates blast radius of modified symbols. | **0 tokens** |

---

## ⚙️ Configuration in ORAGAI

Control Graft behavior in `.env` or `orchestrator/config/__init__.py`:

```ini
# Enable or disable Graft injection into agent context
GRAFT_ENABLED=true

# Cache expiration for pre-computed graft graphs (seconds)
GRAFT_MAX_AGE_SECONDS=300.0
```

| Parameter | Environment Variable | Type | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `graft.enabled` | `GRAFT_ENABLED` | `bool` | `true` | Automatically injects structural maps into Architect and Developer context. |
| `graft.max_age_seconds` | `GRAFT_MAX_AGE_SECONDS` | `float` | `300.0` | Reuses cached graft graph within 5 minutes to avoid redundant rebuilds. |

---

## 🎯 Best Practices for Agents & Developers

1. **Orientation First:** Never read complete files to understand project layout. Use `graft map` or the injected Graft section in your prompt.
2. **Interface Inspection:** Before modifying a module, run `graft skeleton <path/to/module.py>` to examine class definitions, type hints, and parameter contracts.
3. **Pre-Commit Verification:** Run `graft blast` before committing modifications to confirm that no unintended module boundaries or interfaces were broken.
4. **Fallback Safety:** When developing in environments without Graft installed, ORAGAI automatically degrades to native AST symbol checks and directory virtualizers without failing pipeline runs.
