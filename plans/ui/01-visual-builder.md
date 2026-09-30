# UI Plan 01: Visual Studio & Workflow Builder

## 1. Objective
Design the Visual Studio & Workflow Builder UI architecture for ORAGAI, enabling drag-and-drop workflow graph creation, component wiring, live execution inspection, real-time event streaming, and human-in-the-loop interaction without coupling business logic into the UI.

## 2. Current Architecture Involved
- `orchestrator/cli/` (`app.py`, `wizard.py`, `handlers.py`)
- `orchestrator/rendering/` (`output.py`, `diff_renderer.py`, `report_generator.py`)

## 3. Problem
ORAGAI currently relies exclusively on CLI terminal rendering. There is no visual interface for inspecting multi-agent interaction graphs, configuring agent parameters visually, pausing workflows, or viewing live token/progress dashboards.

## 4. Proposed Design

### Client-Server Architecture
The Visual Studio UI is a decoupled web client (React / Next.js / React Flow) communicating with ORAGAI Core via FastAPI REST & WebSocket APIs:

```text
┌─────────────────────────────────────────────────────────────────┐
│               Visual Studio Client (React Flow UI)              │
│                                                                 │
│  [Component Palette]       [Visual Canvas]       [Inspector]    │
│  ├── Agents               ┌───────────────┐      ├── Config     │
│  ├── Models               │  [Developer]  │      ├── Model      │
│  ├── Skills               └───────┬───────┘      ├── Skills     │
│  ├── Tools                        ▼              ├── Tools      │
│  └── Verifiers            ┌───────────────┐      └── Telemetry  │
│                           │   [Tester]    │                     │
│                           └───────────────┘                     │
│  ─────────────────────────────────────────────────────────────  │
│  [Execution Controls: Run / Step / Pause]  [Live Event Stream]  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    REST (CRUD) / WebSocket (Events)
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                   ORAGAI API Server (FastAPI)                   │
│                                                                 │
│  /api/v1/graphs          /api/v1/components      /ws/events     │
│  /api/v1/execution       /api/v1/plugins         /ws/terminal   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                    ORAGAI Core & Graph Engine                   │
└─────────────────────────────────────────────────────────────────┘
```

### Visual Builder Capabilities
1. **Component Palette**: Drag-and-drop library of available Agents, Models, Tools, Skills, Memory modules, and Verifiers discovered from the Component Registry.
2. **Visual Graph Canvas**: Node-link diagram connecting input and output ports with real-time port compatibility type validation.
3. **Live Execution Visualizer**: Highlights active executing nodes in real-time, displays turn counts, and streams agent scratchpads.
4. **Human-in-the-Loop Gateway**: Interactive modal prompts when a graph node reaches `requires_approval` or triggers human escalation.
5. **Telemetry & Cost Dashboard**: Live charts rendering token consumption, cost breakdown, stagnation metrics, and verification scores.

## 5. Files/Components Affected
- `orchestrator/ui/server/` (`app.py`, `routes/`, `websocket.py`)
- `orchestrator/ui/client/` (Frontend React / TypeScript SPA)
- `orchestrator/ui/schemas/` (Graph JSON Schema export/import)

## 6. Interfaces/Contracts
```python
from typing import Any, Dict, List
from pydantic import BaseModel

class GraphExportSchema(BaseModel):
    id: str
    name: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Dict[str, float]

class NodeExecutionTelemetry(BaseModel):
    node_id: str
    status: str
    current_turn: int
    tokens_used: int
    cost_usd: float
    last_action: str
    logs: List[str]
```

## 7. Data Flow
User edits graph on canvas -> Canvas JSON posted to `/api/v1/graphs` -> Graph Engine compiles graph -> User clicks "Run" -> Backend dispatches execution -> Event Engine streams live node state updates over WebSocket -> Canvas updates node colors and badges in real time.

## 8. State Transitions
UI Client states: `DISCONNECTED -> CONNECTED -> GRAPH_LOADED -> WORKFLOW_STREAMING -> PAUSED_APPROVAL -> COMPLETED`.

## 9. Error Handling
Network disconnections automatically reconnect WebSocket with session replay recovery from Event Engine ledger.

## 10. Migration Strategy
Develop the API server as an optional headless service (`oragai serve --port 8080`), allowing CLI and UI to operate concurrently on the same engine backend.

## 11. Tests
- Graph JSON export/import round-trip validation tests.
- WebSocket event stream subscription tests.
- API authentication and security header tests.

## 12. Acceptance Criteria
- 100% decoupling: zero business logic in the frontend client.
- Complete visual parity with all CLI-driven multi-agent workflows.

## 13. Dependencies
Depends on Core Engine, Graph Engine, Event Engine, Component Model.

## 14. Risks
WebSocket latency under heavy event volume; mitigated by event throttling and batching on the server bridge.

## 15. Rollback Strategy
CLI interface remains fully functional and autonomous independent of UI availability.
