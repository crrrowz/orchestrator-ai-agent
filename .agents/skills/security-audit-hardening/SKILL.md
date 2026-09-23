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

# Security Auditing & Defensive Hardening Protocol

## 1. Non-Negotiable Security Rules
- **Command Execution**: Never use `shell=True` with dynamic user input. Use parameterized argument lists (`subprocess.run(["cmd", arg1, arg2], shell=False)`).
- **Filesystem Security**: Validate and resolve all file paths against the allowed base directory. Reject any path containing `../` or resolving outside the workspace.
- **Secrets Management**: Never commit hardcoded API keys, tokens, or credentials. Always retrieve them via `os.environ` or `.env` files.
- **Data Deserialization**: Never use `pickle.loads` on untrusted data. Use `json` or validated Pydantic models.
- **SQL / Injection Defense**: Use parameterized queries or ORMs; string interpolation in database queries is strictly forbidden.

## 2. Review Checklist
1. Are user inputs strictly validated and sanitized at entry points?
2. Are error messages sanitised so internal stack traces and database schemas are not leaked to clients?
3. Are rate limits, timeouts, and resource caps enforced to prevent Denial of Service (DoS)?
4. Is cryptographic hashing implemented with modern standards (`bcrypt`, `argon2`, `sha256`) rather than deprecated algorithms (`md5`, `sha1`)?

## 3. Reviewer Action
Any detected violation of these rules requires an immediate `VERDICT: REJECTED` with specific remediation instructions.
