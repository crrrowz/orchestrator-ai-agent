# 🐳 ORAGAI Docker Architecture & Operations Guide

> Comprehensive guide for running, developing, and testing ORAGAI in Docker across both Local and Remote virtual machine environments.

---

## 🌟 Overview: Two Development Architectures

Choose the architecture that matches how Docker is set up on your machine:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   ARCHITECTURE 1: LOCAL DOCKER ENGINE                            │
│  (Host = Windows / macOS / Linux with Docker Desktop or native Docker daemon)     │
│                                                                                  │
│   Windows Host (Editor) <═════ Live Bind Mount (-v) ═════> Container Engine     │
│   - Python edits reflect instantly without rebuilding images.                    │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                   ARCHITECTURE 2: REMOTE DOCKER ENGINE (SSH CONTEXT)             │
│  (Host = Windows editing files  │  Remote = Debian VM / Server running dockerd)   │
│                                                                                  │
│   Windows Host (Editor) ──[SSH docker build]──> Debian VM (Image with code)      │
│   - Windows and Debian have separate filesystems (no cross-machine -v mount).    │
│   - Rebuilding the code layer takes only 1-2 seconds thanks to uv caching.       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Architecture 1: Local Docker Setup (Docker Desktop or Native Linux)

### Characteristics
* Your code editor and the Docker engine reside on the **same physical filesystem**.
* Live bind mounting (`-v ${PWD}:/workspace/orchestrator-ai-agent` or `docker compose`) links files directly into the container.
* Any edits in Python files take effect immediately with **zero image rebuilds**.

### Workflow Commands
```bash
# 1. Build the development image once:
docker build --target development -t oragai:dev .

# 2. Run with live bind mount (all code edits apply instantly):
docker run --rm -it --env-file .env -v ${PWD}:/workspace/orchestrator-ai-agent oragai:dev python -m orchestrator.main --check-config

# 3. Run automated tests:
docker run --rm -v ${PWD}:/workspace/orchestrator-ai-agent oragai:dev pytest tests/ -v

# 4. Or develop via Dev Containers (VS Code / Antigravity IDE):
# Press Ctrl+Shift+P -> "Dev Containers: Reopen in Container"
```

---

## 🌐 Architecture 2: Remote Docker Setup (Debian VM via SSH Context)

### Characteristics
* You edit code on Windows, but the Docker CLI communicates with an external Linux machine (e.g. `debian-vm` at `192.168.85.129`) over SSH.
* **Why `-v ${PWD}:...` doesn't work directly:** The remote daemon searches for paths on the *Debian filesystem*, not your Windows drive (`D:\...`).
* **The Solution:** `docker build` transfers your workspace code across SSH and bakes it into the container. Because all packages are pre-cached in `/opt/venv`, subsequent builds take only **1 to 2 seconds**.

### Standard Workflow (Fast Rebuilds)
```powershell
# 1. Build and auto-clean dangling images in one step:
docker build --target development -t oragai:dev . ; docker image prune -f

# 2. Run your task or tests:
docker run --rm --env-file .env oragai:dev python -m orchestrator.main --check-config
docker run --rm --env-file .env oragai:dev pytest tests/ -v
```

### Optional Live-Sync Alternative
If you want live sync on Architecture 2 without rebuilding:
1. Configure a **VM Shared Folder** (e.g., via VMware, VirtualBox, or Samba/NFS) mapping your Windows project directory to `/mnt/oragai` inside Debian.
2. Run with the remote path mount:
   ```bash
   docker run --rm -it --env-file .env -v /mnt/oragai:/workspace/orchestrator-ai-agent oragai:dev pytest tests/ -v
   ```

---

## 🔄 When Do You Need to Rebuild? (Comparison Matrix)

| Change Type | Architecture 1 (Local Engine) | Architecture 2 (Remote Debian VM) | Explanation |
| :--- | :---: | :---: | :--- |
| **`.env` File** (API keys, models, configs) | ❌ **Never** | ❌ **Never** | Injected dynamically at runtime via `--env-file .env`. Never baked into image layers. |
| **Python Code** (`.py` files) | ❌ **No Rebuild** (Live `-v` Mount) | ⚠️ **Quick Rebuild** (~1–2s) | Instant with live mount; requires quick `docker build` on remote VM (unless shared folder is used). |
| **Dependencies** (`pyproject.toml` / `uv.lock`) | ✅ **Yes** | ✅ **Yes** | Required so `uv sync` downloads and updates packages inside `/opt/venv`. |
| **System Tools / Base Image** (`Dockerfile`) | ✅ **Yes** | ✅ **Yes** | Required to apply changes to OS packages, build tools, or base configuration. |

---

## 🛠️ Complete Docker Command Reference

### 1. Configuration
```bash
cp .env.example .env
# Edit .env and supply your OPENROUTER_API_KEY, GEMINI_API_KEY, etc.
```

### 2. Building Images
```bash
# Build development image (interactive work, tests, cached dependencies)
docker build --target development -t oragai:dev .

# Build production runner (standalone self-contained image)
docker build --target production -t oragai:latest .

# Build with Docker Compose (if compose plugin is installed)
docker compose build
```

### 3. Running Tasks & Tests
```bash
# Verify system configuration offline (0 tokens consumed)
docker run --rm --env-file .env oragai:dev python -m orchestrator.main --check-config

# Run full test suite (469 automated tests) inside Linux container
docker run --rm oragai:dev pytest tests/ -v

# Execute an autonomous engineering task
docker run --rm -it --env-file .env oragai:dev python -m orchestrator.main "Build a rate limiter" --mode dev-test

# Open interactive bash shell inside container
docker run --rm -it oragai:dev bash
```

### 4. Running with Docker Compose (Optional)
If `docker compose` is available on your machine:
```bash
# Verify configuration
docker compose run --rm cli --check-config

# Execute tasks
docker compose run --rm cli "Build a rate limiter" --mode dev-test

# Run tests
docker compose run --rm test

# Start persistent dev environment
docker compose up -d dev
docker compose exec dev bash
```

### 5. Creating & Managing the Docker Context (`debian-vm`)

If you run Docker inside a Debian virtual machine (VMware, VirtualBox, or external Linux server) while using the Docker CLI on Windows, here is the complete step-by-step setup:

#### Step A: Prerequisites on the Debian VM (One-time)
1. **Ensure Docker is installed and running:**
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io
   sudo systemctl enable --now docker
   ```
2. **Add your Linux user to the `docker` group** (avoids needing `sudo` for Docker):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```
3. **Verify OpenSSH server is running:**
   ```bash
   sudo systemctl status ssh
   ```
4. **Find your VM's IP address:**
   ```bash
   ip -4 addr show
   ```

#### Step B: Set Up Passwordless SSH from Windows (One-time)
To allow Docker CLI to connect over SSH without prompting for passwords:
```powershell
# 1. Generate SSH key on Windows (if you don't already have one)
ssh-keygen -t ed25519 -N '""'

# 2. Copy your Windows public key into Debian VM's authorized_keys
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh crowz-debian@192.168.85.129 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"

# 3. Test passwordless connection
ssh crowz-debian@192.168.85.129 "docker info"
```

#### Step C: Create the Docker Context on Windows
Once passwordless SSH works, register the remote engine in Docker CLI:
```powershell
# Create the context pointing to your Debian VM
docker context create debian-vm --docker "host=ssh://crowz-debian@192.168.85.129"

# Switch to the new context
docker context use debian-vm

# Verify the active context
docker context show
docker info
```

#### Step D: Managing & Updating Contexts
```powershell
# List all registered contexts
docker context ls

# If the VM IP address changes (e.g. via DHCP), update the context:
docker context update debian-vm --docker "host=ssh://crowz-debian@<NEW_IP>"

# Switch back to local Windows Docker (if installed)
docker context use default

# Remove context if no longer needed
docker context rm debian-vm
```

#### Step E: Troubleshooting `Connection timed out / Error 255`
If you encounter `stderr=banner exchange: Connection timed out`:
1. **VM is paused/sleeping:** Check VMware / VirtualBox and ensure the Debian VM is awake and running.
2. **IP address changed:** Run `ip a` on Debian to verify whether DHCP assigned a new IP, then run `docker context update debian-vm --docker "host=ssh://crowz-debian@<NEW_IP>"`.
3. **Test SSH port:** Run `Test-NetConnection -ComputerName 192.168.85.129 -Port 22` from Windows PowerShell.

> [!NOTE]
> If you are using the standalone Docker CLI on Windows without Docker Desktop, there is no local engine on Windows. When the Debian VM is shut down, Docker commands will be unavailable until the VM is restarted.

### 6. Cleaning Dangling Images (`dangling=true`)
Rebuilding images repeatedly creates untagged intermediate layers (`<none>:<none>`). Clean them safely without touching active images:
```powershell
# List all dangling images
docker images -f "dangling=true"

# Prune all dangling images safely
docker image prune --filter "dangling=true" -f

# Single-command build and auto-clean (recommended for Architecture 2)
docker build --target development -t oragai:dev . ; docker image prune -f

# Deep system cleanup (reclaims unused volumes, networks, and build cache)
docker system prune -f
docker system prune -a --volumes -f
```

### 7. Dev Containers (VS Code / Antigravity IDE)
1. Open the project folder in your IDE.
2. Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on macOS).
3. Select **Dev Containers: Reopen in Container**.
4. The IDE connects directly into the Linux Docker environment with Python, `uv`, and all tools pre-configured.
