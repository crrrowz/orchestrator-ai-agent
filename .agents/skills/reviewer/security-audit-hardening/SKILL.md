---
name: security-audit-hardening
description: Comprehensive security auditing and defensive hardening skill. Prevents OWASP Top 10 vulnerabilities, command injection, path traversal, secret leaks, and insecure deserialization.
triggers:
  - security
  - audit
  - vulnerability
  - sanitize
  - auth
  - token
---

# Security Auditing & Hardening

## 1. Non-Negotiable Invariants
- Command Execution: Always pass argument lists with `shell=False`. Banish `shell=True` on dynamic input.
- Path Security: Resolve and validate paths against workspace root. Forbid relative `../` escapes.
- Secrets: Never commit API keys or tokens. Retrieve via environment variables or `.env`.
- Deserialization: Use `json` or validated Pydantic models. Forbid untrusted `pickle.loads`.

## 2. Reviewer Action
- Any identified security violation requires immediate `VERDICT: REJECTED` with explicit mitigation steps.
