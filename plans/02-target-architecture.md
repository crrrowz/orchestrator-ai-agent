# Plan 02: Target Architecture Specification

## 1. Objective
Define the target architecture for ORAGAI as a modular, visual, engine-based autonomous AI platform. Establish formal boundaries, protocols, and data contracts across all 13 core engines and component layers.

## 2. Current Architecture Involved
- Monolithic orchestration (`orchestrator/orchestrator.py`, `pipeline/`, `agents/`, `control/`, `sentinel/`).

## 3. Problem
Lack of clean architectural boundaries, modularity, visual composability, and extensibility. Hardcoded agent and pipeline wiring prevents runtime graph construction, dynamic model swapping, and third-party plugin integration.

## 4. Proposed Design

### Target Architectural Topology

```text
                               ┌─────────────────────────────────────────┐
                               │       Visual Studio / UI Client         │
                               └────────────────────┬────────────────────┘
                                                    │ REST / WebSocket
                               ┌────────────────────▼────────────────────┐
                               │           ORAGAI Core Engine            │
                               └──────┬───────────────────────────┬──────┘
                                      │                           │
                   ┌──────────────────▼───────────┐   ┌───────────▼──────────────────┐
                   │         Graph Engine         │   │         Plugin Engine        │
                   └──────────┬───────────────────┘   └───────────┬──────────────────┘
                              │                                   │
       ┌──────────────────────┼───────────────────────────────────┼──────────────────────┐
       │                      │                                   │                      │
┌──────▼──────┐        ┌──────▼──────┐                     ┌──────▼──────┐        ┌──────▼──────┐
│Agent Engine │        │Task Engine  │                     │Model Engine │        │Skill Engine │
└──────┬──────┘        └──────┬──────┘                     └──────┬──────┘        └──────┬──────┘
       │                      │                                   │                      │
       │               ┌──────▼──────────────┐                    │               ┌──────▼──────┐
       ├──────────────►│  Execution Engine   │◄───────────────────┴──────────────►│ Tool Engine  │
       │               └──────┬──────────────┘                                    └─────────────┘
       │                      │
┌──────▼──────┐        ┌──────▼──────────────┐                     ┌─────────────┐
│Memory Engine│        │  Governance Engine  │◄────────────────────┤Event Engine │
└─────────────┘        └──────┬──────────────┘                     └──────┬──────┘
                              │                                           │
                       ┌──────▼──────────────┐                            │
                       │ Verification Engine │◄───────────────────────────┘
                       └─────────────────────┘
```

### Engine Subsystem Boundaries & Specifications

#### 1. Core Engine
- **Responsibility**: System bootstrap, configuration resolution, lifecycle orchestration, and engine registry.
- **Inputs**: CLI flags, environment variables, YAML/JSON project configurations.
- **Outputs**: Initialized runtime context, engine registry.
- **Dependencies**: None (root bootstrap).
- **Public API**: `CoreRuntime.bootstrap()`, `CoreRuntime.get_engine(name)`.
- **State Ownership**: Global runtime lifecycle status.
- **Failure Behavior**: Fatal startup exit on unrecoverable configuration or dependency errors.
- **Extension Mechanism**: Engine registration hooks.

#### 2. Graph Engine
- **Responsibility**: Representation, compilation, validation, and step-by-step traversal of execution DAGs/cycles.
- **Inputs**: Declarative Graph definitions (JSON/YAML/Visual graph schemas).
- **Outputs**: Node execution dispatches, graph completion state.
- **Dependencies**: Core Engine, Event Engine.
- **Public API**: `GraphEngine.load_graph()`, `GraphEngine.execute()`, `GraphEngine.step()`.
- **State Ownership**: Execution graph topology, node states, port data caches.
- **Failure Behavior**: Transitions failing node to ERROR state; triggers edge error routing or recovery policies.
- **Extension Mechanism**: Custom node types, edge evaluators, loop controllers.

#### 3. Agent Engine
- **Responsibility**: Dynamic assembly of agents by combining Model, Skills, Tools, Memory, and Governance specs.
- **Inputs**: Agent configuration schemas.
- **Outputs**: Instantiated, executable Agent instances.
- **Dependencies**: Model Engine, Skill Engine, Tool Engine, Memory Engine, Governance Engine.
- **Public API**: `AgentEngine.create_agent(config)`, `AgentEngine.register_agent_template(schema)`.
- **State Ownership**: Agent configurations, active agent session instances.
- **Failure Behavior**: Graceful agent termination with diagnostics capture.
- **Extension Mechanism**: Agent archetypes, persona injectors.

#### 4. Model Engine
- **Responsibility**: Provider-agnostic LLM interface, token estimation, rate-limiting, and cost tracking.
- **Inputs**: Prompt contexts, structured output schemas, tool declarations.
- **Outputs**: Standardized LLM completions, tool calls, token usage metadata.
- **Dependencies**: Core Engine, Event Engine.
- **Public API**: `ModelEngine.generate()`, `ModelEngine.stream()`, `ModelEngine.get_pricing()`.
- **State Ownership**: Model provider adapters, connection pools.
- **Failure Behavior**: Provider fallback, exponential backoff retry on HTTP 429/5xx.
- **Extension Mechanism**: Custom provider adapters (OpenAI, Anthropic, Google, Local, OpenRouter).

#### 5. Tool Engine
- **Responsibility**: Tool registration, sandboxing, AST security inspection, and execution isolation.
- **Inputs**: Tool invocation requests (command/arguments).
- **Outputs**: Tool execution artifacts, stdout/stderr, execution metadata.
- **Dependencies**: Core Engine, Event Engine.
- **Public API**: `ToolEngine.register_tool()`, `ToolEngine.execute(tool_name, params)`.
- **State Ownership**: Tool registry, sandbox environments.
- **Failure Behavior**: Sandboxed exception isolation, blocked command escalation triggers.
- **Extension Mechanism**: Third-party tool plugin descriptors.

#### 6. Skill Engine
- **Responsibility**: Skill discovery, dependency resolution, dynamic prompt compilation, and token compression.
- **Inputs**: Skill names, task requirements, token budget constraints.
- **Outputs**: Injected system instructions, reference examples, skill metadata.
- **Dependencies**: Core Engine, Memory Engine.
- **Public API**: `SkillEngine.discover()`, `SkillEngine.resolve(skill_names)`, `SkillEngine.compress()`.
- **State Ownership**: Skill repository, metadata cache.
- **Failure Behavior**: Missing skill fallback to general knowledge with warning.
- **Extension Mechanism**: SKILL.md dynamic loading, remote skill repositories.

#### 7. Memory Engine
- **Responsibility**: Multi-tiered memory management (Conversation, Task, Project, Agent, Long-Term).
- **Inputs**: Context chunks, messages, artifacts, retrieval queries.
- **Outputs**: Semantic search results, compressed context windows, handoff artifacts.
- **Dependencies**: Core Engine, Model Engine (for embeddings).
- **Public API**: `MemoryEngine.store()`, `MemoryEngine.retrieve()`, `MemoryEngine.compact()`.
- **State Ownership**: Vector indices, key-value session stores, handoff storage.
- **Failure Behavior**: Memory fallback to raw FIFO windowing on index corruption.
- **Extension Mechanism**: Storage backends (SQLite, Chroma, Redis, Filesystem).

#### 8. Task Engine
- **Responsibility**: Task decomposition, Milestone DAG management, dependency resolution, and priority queues.
- **Inputs**: High-level task descriptions, user goals.
- **Outputs**: Atomic subtasks, execution sequence, milestone criteria.
- **Dependencies**: Core Engine, Event Engine.
- **Public API**: `TaskEngine.decompose()`, `TaskEngine.get_next_subtask()`, `TaskEngine.update_status()`.
- **State Ownership**: Task dependency DAG, task status records.
- **Failure Behavior**: Dependency blockage propagation, replanning trigger.
- **Extension Mechanism**: Custom task planners, hierarchical milestone strategies.

#### 9. Execution Engine
- **Responsibility**: Unified runtime execution manager, driving Agent interaction loops across pluggable runtimes.
- **Inputs**: Agent instances, Task instructions, Execution policies.
- **Outputs**: Execution turn outcomes, tool call sequences, final artifacts.
- **Dependencies**: Agent Engine, Tool Engine, Model Engine, Event Engine.
- **Public API**: `ExecutionEngine.execute_turn()`, `ExecutionEngine.run_loop()`.
- **State Ownership**: Active execution loops, turn counters, step telemetry.
- **Failure Behavior**: Halts execution turn, raises structured execution fault event.
- **Extension Mechanism**: Runtimes (Native Async Engine, OpenHands Bridge, Docker Isolated Runner).

#### 10. Governance Engine
- **Responsibility**: Multi-dimensional execution governance (tokens, budget, stagnation, chaos, AST guards).
- **Inputs**: Real-time telemetry, tool invocation intents, token consumption, state transitions.
- **Outputs**: Governance verdicts (`CONTINUE`, `EXTEND_BUDGET`, `REPLAN`, `RETRY`, `DECOMPOSE`, `HALT`).
- **Dependencies**: Event Engine, Core Engine.
- **Public API**: `GovernanceEngine.evaluate()`, `GovernanceEngine.check_preflight()`.
- **State Ownership**: Budget trackers, stagnation velocity metrics, circuit breaker states.
- **Failure Behavior**: Deterministic safety halt when hard boundaries or circuit breakers trip.
- **Extension Mechanism**: Custom governance policies, dynamic safety heuristics.

#### 11. Verification Engine
- **Responsibility**: Evidence-based completion verification, test execution parsing, audit gate evaluation.
- **Inputs**: Generated code, execution logs, test outputs, git diffs.
- **Outputs**: Verification verdicts (`VERIFIED`, `REJECTED`), structured defect reports.
- **Dependencies**: Tool Engine, Task Engine, Event Engine.
- **Public API**: `VerificationEngine.verify(task, evidence)`, `VerificationEngine.run_suite()`.
- **State Ownership**: Verification criteria catalog, evidence ledgers.
- **Failure Behavior**: Emits structured feedback directly to Graph Engine for remediation routing.
- **Extension Mechanism**: Custom verifiers (PyTest, Sonar, Security Linter, Architectural Guard).

#### 12. Event Engine
- **Responsibility**: Asynchronous, high-throughput Pub/Sub event bus decoupling all engines.
- **Inputs**: Typed Event payloads from any engine or component.
- **Outputs**: Dispatched event notifications to registered subscribers.
- **Dependencies**: None (Core primitive).
- **Public API**: `EventEngine.publish(event)`, `EventEngine.subscribe(topic, handler)`.
- **State Ownership**: In-memory and persisted event queues, subscriber registries.
- **Failure Behavior**: Isolated subscriber exception handling; unhandled events logged to dead-letter queue.
- **Extension Mechanism**: Persistence bridges (SQLite, Kafka, Redis).

#### 13. Plugin Engine
- **Responsibility**: Dynamic discovery, validation, dependency resolution, and sandboxed lifecycle management of plugins.
- **Inputs**: Plugin packages, directory paths, plugin manifests (`manifest.json`/`plugin.yaml`).
- **Outputs**: Registered components (Agents, Tools, Skills, Models, Nodes, Verifiers).
- **Dependencies**: Core Engine, Event Engine.
- **Public API**: `PluginEngine.load_plugin()`, `PluginEngine.discover()`, `PluginEngine.unload_plugin()`.
- **State Ownership**: Loaded plugin manifests, component registry.
- **Failure Behavior**: Faulty plugin quarantine; isolates failure without bringing down the core system.
- **Extension Mechanism**: Plugin manifest v1 spec, dynamic Python import loader.

## 5. Files/Components Affected
New modular package structure under `orchestrator/`:
- `orchestrator/core/`
- `orchestrator/engines/` (`graph/`, `agents/`, `models/`, `tools/`, `skills/`, `memory/`, `tasks/`, `execution/`, `governance/`, `verification/`, `events/`, `plugins/`)
- `orchestrator/ui/`

## 6. Interfaces/Contracts
All engine communication occurs through typed Pydantic models and Abstract Base Classes (Protocols).

## 7. Data Flow
Graph Engine schedules nodes -> Execution Engine invokes Agent -> Agent calls Tools via Tool Engine -> Telemetry published to Event Engine -> Governance Engine evaluates -> Verification Engine validates -> Result stored in Memory Engine.

## 8. State Transitions
System-level state machine: `INITIALIZING -> READY -> EXECUTING -> GOVERNING -> VERIFYING -> COMPLETED/FAILED`.

## 9. Error Handling
Hierarchical error handling: Engine Local -> Graph Node Router -> Governance Circuit Breaker -> Core Emergency Stop.

## 10. Migration Strategy
Incremental engine migration starting from Core & Events, wrapping legacy pipelines in Graph adapters.

## 11. Tests
Engine boundary integration tests, contract conformance tests, and end-to-end multi-agent execution tests.

## 12. Acceptance Criteria
- Clear, unambiguous specifications for all 13 engines.
- Formal definitions of responsibility, inputs, outputs, public API, state, failure behavior, and extensions for every engine.
- Complete decoupling of visual builder and UI logic from engine internals.

## 13. Dependencies
Depends on Plan 00 and Plan 01. Blocks Plans 03 through 13.

## 14. Risks
Interface churn during implementation; mitigated by freezing Pydantic protocol definitions early in Phase 4.

## 15. Rollback Strategy
Engine interfaces designed to run alongside legacy pipeline shims.
