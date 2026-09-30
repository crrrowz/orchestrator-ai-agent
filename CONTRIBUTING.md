# Contributing to ORAGAI

Thank you for your interest in contributing to **ORAGAI**! We are building the next generation of autonomous, resilient multi-agent software engineering systems.

---

## 📜 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Development Setup](#development-setup)
3. [Branching & Workflow](#branching--workflow)
4. [Architecture Invariants](#architecture-invariants)
5. [Testing & Quality Assurance](#testing--quality-assurance)
6. [Submitting Pull Requests](#submitting-pull-requests)
7. [Reporting Issues](#reporting-issues)

---

## Code of Conduct

All contributors are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all participants with respect and professional courtesy.

---

## Development Setup

### Prerequisites
- **Python 3.12+**
- **uv** (recommended) or `pip`
- **Git**

### Installation

```bash
# Fork & clone the repo
git clone https://github.com/YOUR_USERNAME/orchestrator-ai-agent.git
cd orchestrator-ai-agent

# Create virtual environment and install all dependencies
uv sync

# Copy environment template
cp .env.example .env
```

---

## Branching & Workflow

1. Create a new topic branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
2. Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)`: New capability
   - `fix(...)`: Bug fix
   - `test(...)`: Adding or updating tests
   - `docs(...)`: Documentation changes
   - `refactor(...)`: Code refactoring without behavioral change

---

## Architecture Invariants

When contributing to ORAGAI, respect these strict architectural rules:

1. **Hexagonal Boundaries**: All external side-effects (file I/O, subprocesses, LLM API calls, Git) MUST pass through driven ports in `orchestrator/ports/driven/`.
2. **Zero-Token First**: Always favor static AST/parser inspection over burning LLM tokens where possible.
3. **Deterministic Governance**: Do NOT introduce unstructured LLM prompt loops without state machine transitions.
4. **RBAC Tool Scoping**: Agents must only write within their designated directory prefixes.
5. **Cross-Platform Compatibility**: Code must run identically on both Linux and Windows.

---

## Testing & Quality Assurance

Every Pull Request must pass the full test suite without regressions:

```bash
# Run full test suite
uv run pytest tests/ -v

# Run linting with Ruff
uv run ruff check .

# Validate configuration loading
uv run python -m orchestrator.main --check-config
```

---

## Submitting Pull Requests

1. Ensure all tests pass locally.
2. Update relevant documentation in `docs/` if modifying interfaces or behavior.
3. Keep pull requests focused on a single change.
4. Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).
5. A project maintainer will review your contribution.

---

## Reporting Issues

Use our [GitHub Issue Templates](.github/ISSUE_TEMPLATE/) to report bugs or request features. Provide complete reproduction steps, error logs, and environment details.
