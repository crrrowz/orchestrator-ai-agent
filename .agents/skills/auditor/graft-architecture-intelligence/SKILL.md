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

# Graft Codebase Intelligence

## 1. Core Commands (Windows NT & PowerShell Compatible)
- Orientation: `graft map`
- Signatures: `graft skeleton <relative_filepath>`
- Callers (inbound): `graft callers <symbol>`
- Dependencies (outbound): `graft callers --direction out <symbol>`
- Impact Analysis: `graft blast`
- Rebuild Graph: `graft build`

## 2. Invariants
- Query `graft skeleton` to inspect interfaces instead of reading complete files.
- Verify `graft blast` before finalizing modifications to contain change scope.
- Use explicit, unchained PowerShell commands.
