---
name: graft-architecture-intelligence
description: Codebase intelligence and wiring graph navigation via Graft CLI. Zero-token repository orientation, clusters, API skeletons, blast radius, and call graphs.
triggers:
  - graft
  - architecture
  - map
  - skeleton
  - callers
  - blast
  - dependency
---

# Graft Codebase Architecture & Intelligence

## 1. Purpose
Enable agents to navigate, analyze, and safely modify complex repositories with zero unnecessary token consumption by querying the local wiring graph built by `graft`.

## 2. Core Commands & Workflows

### A. Repository Orientation (Zero Token Map)
Before reading source files in an existing codebase, run:
```bash
graft map
```
- **Returns**: Directory clusters, hub symbols, and hotspots (heavily coupled files).
- **Efficiency**: Saves ~95% tokens compared to raw directory file reads.

### B. API Surface & Signatures
To inspect a file's public interface, functions, and class definitions without loading the entire implementation:
```bash
graft skeleton <relative_filepath>
```
- **Usage**: Verify method names, parameter types, and return contracts before writing caller code.

### C. Dependency & Call Graph Tracing
To check who depends on or calls a specific function or class:
```bash
graft callers <symbol>
graft callers --direction out <symbol>
```
- **Usage**: Ensure modifications do not break external consumers.

### D. Blast Radius Verification
Before committing code changes, run:
```bash
graft blast
```
- **Returns**: Exactly which modules, tests, and callers are affected by the current diff.

### E. Graph Rebuilding
If significant new files or modules were added:
```bash
graft build
```
- Refreshes the local `graft/` context graph.
