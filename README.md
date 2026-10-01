<div align="center">

<p align="center">
  <img src="imgs/logo-oragai.jpg" alt="ORAGAI Official Logo" width="220" style="border-radius: 50%; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);" />
</p>

# ⚡ ORAGAI

### *Orchestrated Resilient Autonomous Generative AI*

**Experimental Multi-Agent Software Engineering Framework for governed, state-driven, and verifiable AI-assisted software development.**

<br />

<p align="center">
  <img src="imgs/oragai_hero_image.svg" alt="ORAGAI Deterministic Multi-Agent Engineering Architecture" width="100%" />
</p>

---

## ⚠️ IMPORTANT — PROJECT STATUS

> **ORAGAI is currently an unstable and actively evolving project.**
>
> The architecture, orchestration engine, agent workflows, APIs, and internal components are still under development and may change significantly.
>
> **The project currently contains known architectural, implementation, integration, and reliability issues. Some documented features may be incomplete, experimental, partially implemented, or not yet validated in real-world production workloads.**
>
> **Do not consider the current version production-ready.**
>
> The repository should currently be treated as an **experimental engineering project and architectural research platform**, not as a stable production framework.
>
> The goal of the current development phase is to identify architectural weaknesses, simplify the system where necessary, improve reliability, eliminate unnecessary complexity, strengthen verification, and gradually move toward a stable release.
>
> If you use ORAGAI, expect breaking changes, incomplete functionality, failed workflows, and architectural refactoring.

### Current Development Priorities

* 🧱 Stabilizing the core architecture
* 🔍 Identifying and removing architectural weaknesses
* 🐛 Fixing existing implementation and integration problems
* 🔄 Improving orchestration reliability and failure recovery
* 🧪 Strengthening automated verification and test coverage
* 🧠 Improving codebase intelligence and context management
* 💰 Reducing unnecessary LLM/token consumption
* 🔌 Improving provider and tool integrations
* 📐 Simplifying overly complex components
* 📚 Synchronizing documentation with the actual implementation
* 🚀 Establishing a reliable foundation before declaring production readiness

> **The architecture described in this README represents the intended direction of ORAGAI and should not automatically be interpreted as proof that every component is currently complete or production-ready.**

---

## 🏷️ Project Maturity

| Area                       | Current Status              |
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

**ORAGAI** is an experimental multi-agent software engineering framework designed to explore how multiple specialized AI agents can work together under a controlled orchestration layer.

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
              │       ORAGAI CONTROL PLANE             │
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

The objective is to create **controlled interaction between agents**, with explicit evidence, state transitions, and verification rather than relying entirely on free-form agent conversations.

---

## ✨ Core Concepts

| Concept                            | Purpose                                                                                         |
| ---------------------------------- | ----------------------------------------------------------------------------------------------- |
| 🧩 **Modular Architecture**        | Separate orchestration, agents, models, tools, memory, execution, governance, and verification. |
| 🛡️ **Guarded Workflows**          | Control how execution moves between different stages and failure states.                        |
| 🔍 **Codebase Intelligence**       | Build structural understanding of a repository before asking LLMs to reason about it.           |
| 🧠 **Context Handoff**             | Transfer relevant information between specialized agents without repeatedly rebuilding context. |
| 💰 **Token Governance**            | Track and constrain LLM usage to reduce unnecessary consumption.                                |
| 🧪 **Evidence-Based Verification** | Use tests, diagnostics, diffs, and other evidence before considering work complete.             |
| 🔄 **Failure Recovery**            | Detect failures and attempt controlled recovery rather than endlessly retrying.                 |
| 🔌 **Provider Abstraction**        | Allow different LLM providers to participate in the orchestration system.                       |

> These capabilities are part of the project's current architecture and development direction. Their implementation maturity varies across the repository.

---

## ⚡ Quickstart

### Installation

```bash
git clone https://github.com/crrrowz/orchestrator-ai-agent.git
cd orchestrator-ai-agent

uv sync
```

Or:

```bash
uv pip install -e .
```

### Configure Secrets

```bash
cp .env.example .env
```

Edit `.env` and configure the provider credentials required by your environment.

### Verify the Environment

```bash
uv run python -m orchestrator.main --check-config
```

### Run Tests

```bash
uv run pytest tests/ -v
```

> **Note:** Passing tests do not currently imply production readiness. The project is still undergoing architectural and integration changes.

---

## 🐳 Docker

Docker support is available for isolated development and execution.

```bash
docker build --target development -t oragai:dev .

docker run --rm --entrypoint pytest oragai:dev tests/ -v
```

For orchestration:

```bash
docker run --rm -it \
  --env-file .env \
  oragai:dev \
  "Build rate limiter" \
  --mode dev-test
```

For detailed Docker workflows:

[Docker Architecture & Operations Guide](docs/guides/DOCKER_GUIDE.md)

---

## 🎯 Execution Modes

ORAGAI currently explores several orchestration modes:

| Mode               | Flag               | Purpose                                                       |
| ------------------ | ------------------ | ------------------------------------------------------------- |
| **Dev-Test Loop**  | `--mode dev-test`  | Developer → verification → testing → iterative fixing         |
| **Full Pipeline**  | `--mode full`      | Architectural planning → implementation → testing → review    |
| **Codebase Audit** | `--mode audit`     | Repository analysis and architectural/implementation findings |
| **Audit & Fix**    | `--mode audit-fix` | Audit findings followed by attempted remediation              |
| **Documentation**  | `--mode docs`      | Automated documentation workflows                             |

> Some modes and components are still experimental and may change as the architecture evolves.

---

## 🏛️ Architecture

ORAGAI is currently organized around a modular / hexagonal-inspired architecture.

```text
.
├── orchestrator/
│   ├── core/                # Core domain abstractions
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
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Architectural Direction

The intended architecture separates:

```text
Domain
   ↓
Governance
   ↓
Orchestration
   ↓
Agents
   ↓
Execution
   ↓
Verification
   ↓
Recovery / Diagnostics
```

This separation is intended to make the system easier to reason about, test, replace, and evolve.

---

## 🧪 Testing & Verification

The project contains an automated test suite covering multiple architectural layers.

Run:

```bash
uv run pytest tests/ -v
```

or:

```bash
uv run pytest tests/ -q
```

### Important

Test count alone should **not** be interpreted as a guarantee of correctness.

ORAGAI is currently undergoing active architectural changes, and tests may themselves require refinement as the implementation evolves.

The project therefore treats testing as one part of a larger verification process involving:

* Unit tests
* Integration tests
* Workflow validation
* Failure-path testing
* Repository analysis
* Runtime diagnostics
* Architecture review
* Real-world task validation

---

## 🔬 Current Engineering Challenges

The project is intentionally being developed with a strong focus on identifying failure modes.

Some of the areas currently requiring attention include:

### Architecture Complexity

As ORAGAI evolved, multiple abstractions and subsystems were introduced. Some may need to be simplified, merged, redesigned, or removed.

### Agent Reliability

Multi-agent workflows introduce failure modes such as:

* Incorrect assumptions
* Incomplete context
* Repeated work
* Incorrect state transitions
* Endless repair loops
* False completion
* Inconsistent outputs between agents

### Verification

A successful agent response does not necessarily mean that the resulting software is correct.

ORAGAI therefore continues to evolve toward stronger evidence-based completion criteria.

### Token Efficiency

Complex orchestration can introduce significant LLM overhead.

One of the project's goals is to determine where deterministic tooling can replace unnecessary LLM reasoning.

### Documentation Drift

Because the architecture changes rapidly, documentation can temporarily describe intended architecture rather than the exact state of the implementation.

This is an active area of improvement.

---

## 🗺️ Development Philosophy

ORAGAI is not being developed around the assumption that the current architecture is correct.

Instead:

```text
Build
  ↓
Measure
  ↓
Find Failure
  ↓
Understand Root Cause
  ↓
Simplify / Redesign
  ↓
Implement
  ↓
Verify
  ↓
Repeat
```

Existing code is therefore **not automatically considered correct simply because it already exists**.

Architectural decisions are expected to be revisited when evidence shows that they introduce unnecessary complexity, poor reliability, excessive token usage, or maintenance problems.

---

## 📚 Documentation

The documentation is available under [`docs/`](docs/INDEX.md).

Key sections include:

* [Documentation Hub](docs/INDEX.md)
* [Docker Guide](docs/guides/DOCKER_GUIDE.md)
* [Configuration Reference](docs/guides/CONFIG_REFERENCE.md)
* [API & Architecture Reference](docs/architecture/API_REFERENCE.md)
* [Architectural Assessment](docs/architecture/ARCHITECTURAL_ASSESSMENT.md)
* [Code Intelligence Review](docs/architecture/CODE_INTELLIGENCE_REVIEW.md)
* [Failure Analysis](docs/architecture/FAILURE_ANALYSIS.md)
* [Engineering Plans](docs/plans/)
* [Progress Reports](docs/execution/)
* [Documentation Drift Report](docs/reports/DOCUMENTATION_DRIFT_REPORT.md)

---

## 🤝 Contributing

Contributions, experiments, architectural reviews, bug reports, and constructive criticism are welcome.

Before contributing, please read:

* [CONTRIBUTING.md](CONTRIBUTING.md)
* [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## 🛡️ Security

For vulnerability reporting guidelines, see:

[SECURITY.md](SECURITY.md)

---

## 📄 License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full license text.

---

## ⚠️ Final Note

**ORAGAI is a work in progress.**

The project has ambitious architectural goals, but the current implementation does not yet represent the final system.

If you are evaluating ORAGAI, evaluate the **code, tests, implementation status, and documented limitations**, not only the architecture diagrams or feature descriptions.

The project is currently focused on turning the existing experimental foundation into a **simpler, more reliable, better-tested, and genuinely production-capable system**.

</div>
