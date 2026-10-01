<div align="center">

<p align="center">
  <img src="imgs/logo-oragai.jpg" alt="ORAGAI Official Logo" width="220" style="border-radius: 50%; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);" />
</p>

# ⚡ ORAGAI

### *Orchestrated Resilient Autonomous Generative AI*

**Experimental Multi-Agent Software Engineering Framework with Guarded FSM Lifecycle, Codebase Intelligence, Governance & Automated Verification.**

<br />

<p align="center">
  <img src="imgs/oragai_hero_image.svg" alt="ORAGAI Deterministic Multi-Agent Engineering Architecture" width="100%" />
</p>

> **Hero Architecture Diagram:** The ORAGAI multi-agent control plane orchestrating specialized agent personas (*Architect*, *Developer*, *Tester*, *Reviewer*, *Auditor*) with centralized workflow control, codebase intelligence, governance, verification, and recovery mechanisms.

<br />

[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg?logo=python\&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Architecture: Hexagonal](https://img.shields.io/badge/Architecture-Hexagonal%20%2F%20Ports%20%26%20Adapters-orange.svg)](#-architecture--hexagonal-design)
[![Project Status](https://img.shields.io/badge/status-experimental-orange.svg)](#-project-status--important)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker\&logoColor=white)](docs/guides/DOCKER_GUIDE.md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[Features](#-key-innovations) •
[Quickstart](#-quickstart) •
[Architecture](#-architecture--hexagonal-design) •
[Execution Modes](#-execution-modes) •
[Comparison](#-architectural-comparison) •
[Documentation](#-documentation-index)

</div>

---

## ⚠️ Project Status — Important

> **ORAGAI is currently an unstable and actively evolving project.**
>
> This project is **not production-ready** at its current stage.
>
> The repository contains known architectural, implementation, integration, and reliability issues. Some features described in this README are experimental, partially implemented, under development, or represent the intended architectural direction rather than a fully validated production implementation.
>
> The current codebase should be considered an **experimental engineering project and research platform**.
>
> ### Current Development Priorities
>
> * 🐛 Fix existing implementation and integration problems
> * 🧱 Stabilize and simplify the architecture
> * 🔄 Improve orchestration reliability and failure recovery
> * 🧪 Strengthen automated and integration testing
> * 🧠 Improve codebase intelligence and context management
> * 💰 Reduce unnecessary LLM and token consumption
> * 🔌 Improve provider and tool integrations
> * 📚 Eliminate documentation drift
> * 🧩 Remove unnecessary complexity and duplicated abstractions
> * 🚀 Establish a reliable foundation before declaring production readiness
>
> **Breaking changes, incomplete functionality, architectural refactoring, and workflow failures should be expected during development.**
>
> The architecture and diagrams presented below describe the **current design direction and intended system architecture**. They should not be interpreted as a guarantee that every described capability is currently complete, stable, or production-ready.

---

## 🏷️ Project Maturity

| Area                       | Status                      |
| -------------------------- | --------------------------- |
| Core Architecture          | 🟡 Under Active Development |
| Multi-Agent Orchestration  | 🟡 Experimental             |
| FSM / Workflow Engine      | 🟡 Under Development        |
| Codebase Intelligence      | 🟡 Experimental             |
| AST Guard / Self-Healing   | 🟠 Experimental             |
| Multi-Provider LLM Support | 🟡 Under Development        |
| Token Governance           | 🟡 Under Development        |
| Automated Verification     | 🟡 Under Development        |
| Docker Support             | 🟡 Available / Evolving     |
| Documentation              | 🟡 Continuously Updating    |
| Production Readiness       | 🔴 **Not Ready**            |

---

## 💡 What is ORAGAI?

**ORAGAI** is an experimental multi-agent software engineering framework exploring how specialized AI agents can collaborate through a controlled orchestration layer.

Instead of treating AI agents as independent conversational workers, ORAGAI explores a more structured approach based on:

* State-driven execution
* Specialized agent roles
* Explicit workflow transitions
* Codebase intelligence
* Context handoff
* Resource and token governance
* Automated verification
* Failure detection and recovery
* Multi-provider LLM support
* Architectural boundaries between orchestration, execution, and infrastructure

The long-term goal is to build a reliable control plane for AI-assisted software engineering.

However, **the current implementation should be considered experimental**. The architecture is still being evaluated and several parts of the system require further development, simplification, testing, and validation.

---

## 🧭 Design Direction

ORAGAI is being developed around the following architectural idea:

```text
                         USER TASK / SPECIFICATION
                                    │
                                    ▼
              ┌───────────────────────────────────────┐
              │         ORAGAI CONTROL PLANE           │
              │                                       │
              │  Workflow / FSM / Governance          │
              │  Context / Budget / Verification      │
              └───────────────┬───────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
     ARCHITECT            DEVELOPER             TESTER
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
                         REVIEWER
                              │
                              ▼
                           AUDITOR
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Verification / SRE    │
                  │ Recovery / Diagnostics│
                  └───────────────────────┘
```

The objective is not simply to add more agents.

The objective is to create **controlled interaction between agents**, with explicit state transitions, evidence, and verification rather than relying entirely on free-form agent conversations.

---

## ✨ Key Innovations

| Feature                                  | Description                                                                                                                                                            |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧩 **Modular Multi-Engine Architecture** | A modular architecture separating core domain, graph/workflow, agents, models, tools, skills, memory, tasks, execution, governance, verification, events, and plugins. |
| 🛡️ **Guarded FSM & Workflow Engine**    | Controlled state-driven execution with explicit transitions, guards, and support for cyclic and DAG-style workflows.                                                   |
| 🔍 **Codebase Intelligence**             | Repository structure, dependency relationships, call information, and code intelligence can be extracted before expensive LLM reasoning.                               |
| 🩹 **AST Guard & Recovery**              | Experimental protection and recovery mechanisms for detecting and addressing code-level problems before or during execution.                                           |
| 💰 **Token & Resource Governance**       | Attempts to control LLM usage through budgets, iteration limits, stagnation detection, and execution policies.                                                         |
| 🔄 **Multi-Provider Resilience**         | Architecture for working with multiple LLM providers and handling provider-level failures.                                                                             |
| 🏗️ **Component Contracts**              | Typed interfaces and boundaries intended to support reusable orchestration components.                                                                                 |
| 📊 **Evidence-Based Verification**       | Verification based on tests, diagnostics, repository state, diffs, and other available evidence.                                                                       |

> **Important:** These capabilities are at different levels of maturity. Some are experimental, some are partially implemented, and others represent ongoing architectural development.

---

## ⚡ Quickstart

### Prerequisites

* Python 3.12 or 3.13
* `uv`
* Git
* Docker (optional)
* API credentials for the LLM provider required by your configuration

### Installation

```bash
# Clone the repository
git clone https://github.com/crrrowz/orchestrator-ai-agent.git

# Enter the project
cd orchestrator-ai-agent

# Install dependencies
uv sync
```

### Configure Secrets

```bash
cp .env.example .env
```

Edit `.env` and configure the provider credentials required by your environment.

### Verify Configuration

```bash
uv run python -m orchestrator.main --check-config
```

### Run Tests

```bash
uv run pytest tests/ -v
```

Or use concise output:

```bash
uv run pytest tests/ -q
```

> **Note:** Passing tests do not currently imply production readiness. The project is still undergoing architectural and integration changes.

---

## 🧪 Example: Dev-Test Workflow

```bash
uv run python -m orchestrator.main \
  "Build a Sliding Window RateLimiter class with unit tests" \
  --mode dev-test
```

The intended workflow is approximately:

```text
Task
 │
 ▼
Understand
 │
 ▼
Plan
 │
 ▼
Implement
 │
 ▼
Preflight
 │
 ▼
Test
 │
 ├── PASS ───────► Continue
 │
 └── FAIL
        │
        ▼
      Diagnose
        │
        ▼
       Fix
        │
        └──────────────► Test Again
```

The exact execution behavior may change as the orchestration engine evolves.

---

## 🐳 Docker Deployment

ORAGAI provides Docker support for isolated development and execution.

### Build Development Image

```bash
docker build --target development -t oragai:dev .
```

### Run Tests Inside Docker

```bash
docker run --rm \
  --entrypoint pytest \
  oragai:dev \
  tests/ -v
```

### Run an Orchestration Task

```bash
docker run --rm -it \
  --env-file .env \
  oragai:dev \
  "Build rate limiter" \
  --mode dev-test
```

For Docker Compose and remote VM workflows:

**[Docker Architecture & Operations Guide](docs/guides/DOCKER_GUIDE.md)**

---

## 🎯 Execution Modes

ORAGAI currently explores several orchestration modes:

| Mode                 | Flag               | Description                                                    | Intended Personas                      |
| -------------------- | ------------------ | -------------------------------------------------------------- | -------------------------------------- |
| **Dev-Test Loop**    | `--mode dev-test`  | Iterative implementation, verification, testing, and fixing.   | Developer, Tester                      |
| **Full Pipeline**    | `--mode full`      | Architectural planning → implementation → testing → review.    | Architect, Developer, Tester, Reviewer |
| **Codebase Audit**   | `--mode audit`     | Repository analysis and architectural/implementation findings. | Auditor                                |
| **Audit & Auto-Fix** | `--mode audit-fix` | Audit findings followed by attempted remediation.              | Auditor, Developer                     |
| **Documentation**    | `--mode docs`      | Automated documentation workflows.                             | Documentation                          |

> Some modes and components are still experimental and may change as the architecture evolves.

---

# 🏛️ Architecture & Hexagonal Design

The codebase is **inspired by Hexagonal (Ports & Adapters) Architecture** and is currently being refined toward clearer architectural boundaries.

<p align="center">
  <img src="imgs/oragai_architecture.svg" alt="ORAGAI 8-Stage Lifecycle & Control Plane Architecture" width="100%" />
</p>

> **Figure 1: ORAGAI Lifecycle Architecture.** The diagram represents the intended flow from task ingestion and codebase intelligence through planning, governance, agent execution, validation, recovery, and verification.

### Comprehensive Multi-Agent Constellation

<p align="center">
  <img src="imgs/oragai_hero_constellation.svg" alt="ORAGAI Multi-Agent Orbit Constellation" width="100%" />
</p>

> **Figure 2: Multi-Agent Constellation.** The diagram represents the intended relationship between governance, codebase intelligence, specialized agents, execution, protection, and provider infrastructure.

---

## 📁 Repository Structure

```text
.
├── orchestrator/
│   ├── core/                # Core domain abstractions and protocols
│   ├── domain/              # Domain models
│   ├── ports/               # Architectural interfaces
│   ├── governance/          # Workflow and resource governance
│   ├── workstreams/         # Development workflows
│   ├── pipeline/            # Execution pipelines
│   ├── sentinel/            # Recovery and protection systems
│   ├── adapters/            # Runtime and language adapters
│   ├── tools/               # Tooling and sandbox infrastructure
│   ├── llm/                 # LLM providers and routing
│   ├── context/             # Context construction and handoff
│   ├── diagnostics/         # Diagnostics and telemetry
│   └── cli/                 # CLI interface
├── tests/                   # Automated tests
├── docs/                    # Architecture and operational documentation
├── Dockerfile               # Multi-stage container specification
├── docker-compose.yml       # Development and test services
└── pyproject.toml           # Package definition
```

---

## 🔄 Intended Agent Lifecycle

ORAGAI explores a controlled software-engineering lifecycle involving specialized roles.

```text
                    ┌─────────────┐
                    │    TASK     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  ARCHITECT  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  DEVELOPER  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   TESTER    │
                    └──────┬──────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
               FAIL                 PASS
                 │                   │
                 ▼                   ▼
             DEVELOPER          REVIEWER
                 │                   │
                 └─────────┐   ┌─────┘
                           │   │
                           ▼   ▼
                         AUDITOR
                           │
                           ▼
                      VERIFICATION
```

This lifecycle is a design direction rather than a guarantee that every execution path is currently implemented exactly as represented.

---

# 🔍 Architectural Comparison

<p align="center">
  <img src="imgs/manual_agent_vs_oragai.svg" alt="Manual Agent Calls vs ORAGAI Governed Execution" width="100%" />
</p>

> **Figure 3: Isolated Agent Calls vs Governed Execution.** Conceptual comparison between independent agent interactions and an orchestration layer that attempts to coordinate context, budgets, workflow state, verification, and recovery.

<br />

| Capability                  |        ORAGAI        | CrewAI | AutoGen |    LangGraph   |
| --------------------------- | :------------------: | :----: | :-----: | :------------: |
| **Guarded Workflow / FSM**  |    🟡 Experimental   |    —   |    —    | 🟡 Graph-based |
| **Codebase Intelligence**   | 🟡 Graft Integration | Varies |  Varies |     Varies     |
| **AST Protection**          |    🟠 Experimental   |    —   |    —    |        —       |
| **Token Governance**        | 🟡 Under Development | Varies |  Varies |     Varies     |
| **Multi-Provider Support**  |          🟡          |   🟡   |    🟡   |       🟡       |
| **Role-Based Execution**    |          🟡          |   🟡   |    🟡   |       🟡       |
| **Verification / Recovery** | 🟡 Under Development | Varies |  Varies |     Varies     |

> This table describes architectural areas being explored by ORAGAI. It is not intended to claim that competing frameworks lack equivalent functionality or that ORAGAI currently provides a superior implementation.

---

## 🏗️ Architectural Divergence in Practice

<p align="center">
  <img src="imgs/oragai_comparison.svg" alt="Architectural Comparison: Fragmented vs Governed" width="100%" />
</p>

> **Figure 4: Structural Comparison.** Conceptual comparison between fragmented agent execution and an orchestration model with shared context, workflow governance, code intelligence, and verification.

---

# 🧠 Codebase Intelligence

One of the major design goals of ORAGAI is to reduce the amount of raw repository information that must be repeatedly supplied to LLMs.

The project explores the use of structural code intelligence tools such as **Graft** to extract repository information before LLM reasoning.

The intended principle is:

```text
Repository
    │
    ▼
Code Intelligence
    │
    ├── Structure
    ├── Dependencies
    ├── Symbols
    ├── Calls
    └── Relationships
    │
    ▼
Relevant Context
    │
    ▼
LLM Reasoning
```

The objective is to reduce unnecessary context transmission and improve the quality of agent reasoning.

This integration is still evolving and should not be considered a universally solved problem.

---

# 💰 Token & Resource Governance

LLM-based software engineering can become expensive when agents repeatedly:

* Re-read the same files
* Rebuild context
* Repeat failed operations
* Continue after meaningful progress has stopped
* Invoke expensive models unnecessarily
* Generate large outputs that provide little additional value

ORAGAI therefore explores explicit resource governance.

Conceptually:

```text
Task
 │
 ▼
Budget
 │
 ▼
Phase Allocation
 │
 ├── Planning
 ├── Implementation
 ├── Testing
 └── Review
 │
 ▼
Usage Monitoring
 │
 ├── Progress
 ├── Cost
 ├── Iterations
 └── Stagnation
 │
 ▼
Continue / Reduce / Stop / Recover
```

The implementation is still being refined.

---

# 🛡️ Verification & Recovery

A central principle of ORAGAI is:

> **An agent saying that a task is complete is not evidence that the task is complete.**

Verification should rely on observable evidence where possible.

Potential evidence sources include:

* Test results
* Static analysis
* Repository state
* Git diff
* Build results
* Runtime diagnostics
* Security checks
* Configuration validation
* Agent-generated artifacts

The project is continuing to improve the distinction between:

```text
Agent Claim
    ≠
System Evidence
```

---

# 🧪 Testing & Verification

Run the complete test suite with:

```bash
uv run pytest tests/ -v
```

Or:

```bash
uv run pytest tests/ -q
```

The test suite covers multiple architectural layers and workflows.

### Important

Passing tests should **not** currently be interpreted as a guarantee of production readiness.

ORAGAI is undergoing active architectural changes, and tests themselves may require refinement as the implementation evolves.

The project therefore treats testing as one part of a larger verification process involving:

* Unit testing
* Integration testing
* Workflow testing
* Failure-path testing
* Repository analysis
* Runtime diagnostics
* Architecture review
* Real-world task validation

---

# 🔬 Current Engineering Challenges

ORAGAI is intentionally being developed with a strong focus on discovering and addressing failure modes.

## Architecture Complexity

As the project evolved, multiple abstractions and subsystems were introduced.

Some components may eventually need to be:

* Simplified
* Merged
* Replaced
* Redesigned
* Removed

Existing code is not automatically considered correct simply because it already exists.

---

## Agent Reliability

Multi-agent systems introduce failure modes such as:

* Incorrect assumptions
* Incomplete context
* Repeated work
* Incorrect state transitions
* Endless repair loops
* False completion
* Inconsistent outputs
* Context drift

These are active engineering concerns.

---

## Verification

A successful agent response does not necessarily mean that the resulting software is correct.

ORAGAI therefore continues to move toward stronger evidence-based completion criteria.

---

## Token Efficiency

Complex orchestration can introduce significant LLM overhead.

One of the project's goals is to determine where deterministic tooling can replace unnecessary LLM reasoning.

---

## Documentation Drift

Because the architecture changes rapidly, documentation can temporarily describe intended architecture rather than the exact implementation.

Keeping the documentation synchronized with the actual codebase is an active development concern.

---

# 🗺️ Development Philosophy

ORAGAI is not being developed around the assumption that the current architecture is already correct.

Instead, the development cycle is:

```text
Build
  │
  ▼
Measure
  │
  ▼
Find Failure
  │
  ▼
Understand Root Cause
  │
  ▼
Simplify / Redesign
  │
  ▼
Implement
  │
  ▼
Verify
  │
  └──────────────► Repeat
```

The project prioritizes **evidence over assumptions**.

Architectural decisions should be revisited when evidence shows that they introduce:

* Unnecessary complexity
* Poor reliability
* Excessive token usage
* Difficult maintenance
* Weak verification
* Fragile integrations

---

# 📚 Documentation Index

The documentation is organized under [`docs/`](docs/INDEX.md).

### Documentation Hub

* 📖 **[Documentation Hub & Index](docs/INDEX.md)** — Central documentation navigation.

### Guides

* 🐳 **[Docker Architecture & Operations Guide](docs/guides/DOCKER_GUIDE.md)** — Container and remote execution workflows.
* ⚙️ **[Configuration Reference Manual](docs/guides/CONFIG_REFERENCE.md)** — Configuration reference.

### Architecture

* 📖 **[API & Architecture Contract](docs/architecture/API_REFERENCE.md)** — Programmatic API and architecture reference.
* 🔍 **[Architectural Assessment](docs/architecture/ARCHITECTURAL_ASSESSMENT.md)** — Architectural analysis.
* ⚡ **[Native Code Intelligence](docs/architecture/CODE_INTELLIGENCE_REVIEW.md)** — Code intelligence and Graft integration.
* 🔬 **[Orchestration Failure Analysis](docs/architecture/FAILURE_ANALYSIS.md)** — Failure and bottleneck analysis.

### Engineering Plans

* 📐 **[Engineering Plans](docs/plans/)** — Architecture and implementation plans.

### Reports

* 📈 **[Milestone Progress Log](docs/execution/progress.md)** — Development progress.
* 📋 **[Documentation Drift Report](docs/reports/DOCUMENTATION_DRIFT_REPORT.md)** — Documentation synchronization analysis.

---

# 🤝 Contributing

Contributions, experiments, architectural reviews, bug reports, and constructive criticism are welcome.

Before contributing, please read:

* [CONTRIBUTING.md](CONTRIBUTING.md)
* [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

Because the project is currently undergoing architectural changes, contributors should expect that APIs, internal abstractions, and workflows may change.

---

# 🛡️ Security

For vulnerability reporting guidelines, see:

[SECURITY.md](SECURITY.md)

---

# 📄 License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full license text.

---

# ⚠️ Final Note

**ORAGAI is a work in progress.**

The project has ambitious architectural goals, but the current implementation does not yet represent the final system.

If you are evaluating ORAGAI, evaluate the:

* Code
* Tests
* Implementation status
* Known limitations
* Actual execution behavior
* Documentation

—not only the architecture diagrams or feature descriptions.

The current objective is to transform the existing experimental foundation into a **simpler, more reliable, better-tested, and genuinely production-capable system**.

**If you encounter a problem, unexpected behavior, architectural weakness, or incomplete feature, reporting it is valuable.**

---

<div align="center">

### ⚡ ORAGAI

*Exploring a more controlled way to build software with AI.*

</div>
