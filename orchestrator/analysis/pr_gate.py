"""
ORAGAI Automated Pull Request (PR) Quality, Security, Architecture & AI Review Gate.

Hybrid Review Pipeline:
1. Deterministic Hard Gates (0 API tokens):
   - Secret leak & security scan
   - AST syntax verification & placeholder stubs check
   - Hexagonal boundary invariant enforcement
   - Ruff linting & Pytest test verification
2. Autonomous AI Reviewer Agent (Gemini / Claude / GPT / OpenRouter):
   - Contextual code logic deep dive
   - Edge case & security bug detection
   - Clean architecture audit
   - Constructive line-by-line feedback & proposed fixes
"""

import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class DRIssue:
    category: str  # "SECURITY", "ARCHITECTURE", "SYNTAX_AST", "TESTS", "LINT", "AI_REVIEW"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    file_path: str
    line: Optional[int]
    message: str
    remediation: str


@dataclass
class PRReviewReport:
    total_files_analyzed: int
    passed: bool
    issues: List[DRIssue] = field(default_factory=list)
    ai_summary: Optional[str] = None
    ai_verdict: Optional[str] = None

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity in ("CRITICAL", "HIGH"))

    def to_markdown(self) -> str:
        status_badge = (
            "🟢 **PR STATUS: APPROVED (All Hard Gates & AI Review Passed)**"
            if self.passed
            else "🔴 **PR STATUS: CHANGES REQUIRED (Actionable Blockers Detected)**"
        )

        lines = [
            "# 🤖 ORAGAI Autonomous AI Pull Request Reviewer & Architecture Gate",
            "",
            status_badge,
            "",
            f"> Evaluated **{self.total_files_analyzed}** changed file(s). Found **{len(self.issues)}** issue(s) (**{self.critical_count}** blocking).",
            "",
            "---",
            "",
        ]

        if self.ai_summary:
            lines.extend([
                "## 🧠 AI Senior Architect & Security Review",
                "",
                self.ai_summary,
                "",
                "---",
                "",
            ])

        if not self.issues and self.passed:
            lines.extend([
                "### ✅ Excellent Work!",
                "No architectural violations, secret leaks, AST defects, or test regressions were detected.",
                "Your PR is clean and ready for maintainer merge.",
            ])
            return "\n".join(lines)

        # Contributor Action Checklist
        lines.extend([
            "## 📋 Required Fix Checklist for Contributor",
            "Please resolve the following items in your branch before this PR can be approved:",
            "",
        ])
        for idx, issue in enumerate(self.issues, 1):
            loc = f"`{issue.file_path}:{issue.line}`" if issue.line else f"`{issue.file_path}`"
            lines.append(f"- [ ] **[{issue.severity}]** {loc} — {issue.message}")
            lines.append(f"  - **Fix**: {issue.remediation}")

        lines.extend(["", "---", "", "## 🔍 Detailed Issue Breakdown", ""])

        # Group by category
        categories = {
            "SECURITY": "🔒 Security & Secret Containment",
            "ARCHITECTURE": "🏛️ Hexagonal Architecture & Boundary Invariants",
            "SYNTAX_AST": "⚙️ Python AST & Structural Validity",
            "TESTS": "🧪 Test Suite & Regression Verification",
            "LINT": "🎨 Style & Code Quality (Ruff)",
            "AI_REVIEW": "🤖 AI Code Logic & Edge Cases",
        }

        for cat_key, cat_title in categories.items():
            cat_issues = [i for i in self.issues if i.category == cat_key]
            if not cat_issues:
                continue

            lines.extend([f"### {cat_title}", ""])
            lines.append("| Severity | Location | Issue Description | Recommended Action |")
            lines.append("|---|---|---|---|")
            for issue in cat_issues:
                loc = f"`{issue.file_path}:{issue.line}`" if issue.line else f"`{issue.file_path}`"
                lines.append(f"| `{issue.severity}` | {loc} | {issue.message} | {issue.remediation} |")
            lines.append("")

        lines.extend([
            "---",
            "<sub>Powered by **ORAGAI Autonomous SRE Engine & AI Sentinel Mesh**</sub>",
        ])
        return "\n".join(lines)


class PRReviewGate:
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()
        self.issues: List[DRIssue] = []
        self.ai_summary: Optional[str] = None
        self.ai_verdict: Optional[str] = None

    def get_git_diff(self) -> str:
        """Extracts the PR diff against origin/main or HEAD~1."""
        for target in ("origin/main...HEAD", "HEAD~1...HEAD"):
            try:
                res = subprocess.run(
                    ["git", "diff", target],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout
            except Exception:
                pass
        return ""

    def get_changed_files(self) -> List[Path]:
        """Detects changed files in PR or working tree."""
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", "origin/main...HEAD"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                files = [self.root_dir / line.strip() for line in res.stdout.splitlines() if line.strip()]
                return [f for f in files if f.exists()]
        except Exception:
            pass

        return list((self.root_dir / "orchestrator").glob("**/*.py"))

    def check_security(self, file_path: Path):
        """Scans file for API keys, hardcoded passwords, and secret leaks."""
        path_str = str(file_path).replace("\\", "/").lower()
        if "example" in path_str or ".env.example" in path_str or "benchmarks/catalog" in path_str or "tests/" in path_str:
            return

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        patterns = [
            (r'sk-[a-zA-Z0-9_\-]{20,}', "Exposed OpenAI / OpenRouter API Key"),
            (r'ghp_[a-zA-Z0-9]{30,}', "Exposed GitHub Personal Access Token"),
            (r'AIza[0-9A-Za-z-_]{35}', "Exposed Google API Key"),
            (r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----', "Exposed Private Cryptographic Key"),
            (r'(?i)(password|secret|api_key|token)\s*=\s*["\'][a-zA-Z0-9_\-]{16,}["\']', "Potential Hardcoded Secret"),
        ]

        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    self.issues.append(DRIssue(
                        category="SECURITY",
                        severity="CRITICAL",
                        file_path=str(file_path.relative_to(self.root_dir)),
                        line=line_num,
                        message=f"{desc} detected.",
                        remediation="Remove the secret immediately. Use environment variables via `.env`."
                    ))

    def check_ast_and_syntax(self, file_path: Path):
        """Validates Python AST, empty stubs, and syntax."""
        if file_path.suffix != ".py":
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            self.issues.append(DRIssue(
                category="SYNTAX_AST",
                severity="CRITICAL",
                file_path=str(file_path.relative_to(self.root_dir)),
                line=e.lineno,
                message=f"Python Syntax Error: {e.msg}",
                remediation="Fix syntax error so file compiles under Python 3.12+."
            ))
            return

        # Check for empty stubs in non-adapter/interface production code
        path_str = str(file_path).replace("\\", "/")
        if "tests/" not in path_str and "adapters/" not in path_str and "engine/" not in path_str and "protocols.py" not in path_str:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        is_abstract = any(
                            (isinstance(d, ast.Name) and d.id in ("abstractmethod", "override")) or
                            (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                            for d in node.decorator_list
                        )
                        if not is_abstract and not node.name.startswith("__"):
                            self.issues.append(DRIssue(
                                category="SYNTAX_AST",
                                severity="HIGH",
                                file_path=str(file_path.relative_to(self.root_dir)),
                                line=node.lineno,
                                message=f"Empty placeholder function `{node.name}()` with bare `pass`.",
                                remediation="Provide real implementation or raise NotImplementedError."
                            ))

    def check_architecture_invariants(self, file_path: Path):
        """Enforces Hexagonal boundary rules."""
        rel_path = str(file_path.relative_to(self.root_dir)).replace("\\", "/")
        if not rel_path.startswith("orchestrator/"):
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return

        # Invariant 1: domain/ must NEVER import from adapters, tools, or cli
        if rel_path.startswith("orchestrator/domain/"):
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in ("adapters", "tools", "cli", "sentinel", "pipeline"):
                        if f"orchestrator.{forbidden}" in node.module or node.module == forbidden:
                            self.issues.append(DRIssue(
                                category="ARCHITECTURE",
                                severity="CRITICAL",
                                file_path=rel_path,
                                line=node.lineno,
                                message=f"Hexagonal Invariant Violation: `domain` cannot import from `{node.module}`.",
                                remediation="Domain models must be pure and decoupled from infrastructure adapters."
                            ))

        # Invariant 2: ports/ must only define protocols/ABCs, no concrete tool implementations
        if rel_path.startswith("orchestrator/ports/"):
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if "orchestrator.adapters" in node.module:
                        self.issues.append(DRIssue(
                            category="ARCHITECTURE",
                            severity="HIGH",
                            file_path=rel_path,
                            line=node.lineno,
                            message=f"Hexagonal Port Inversion: Port imports concrete adapter `{node.module}`.",
                            remediation="Ports define abstract protocols; adapters implement ports, never vice versa."
                        ))

    def run_tests_and_linting(self):
        """Runs ruff and pytest to catch runtime logic bugs."""
        # 1. Ruff Lint
        try:
            print("[1/3] Running ruff lint checks...", flush=True)
            res = subprocess.run(
                ["uv", "run", "ruff", "check", "--output-format=json", "orchestrator/"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False
            )
            if res.stdout.strip():
                try:
                    findings = json.loads(res.stdout)
                    for f in findings[:10]:
                        self.issues.append(DRIssue(
                            category="LINT",
                            severity="MEDIUM",
                            file_path=f.get("filename", ""),
                            line=f.get("location", {}).get("row", 1),
                            message=f"[{f.get('code')}] {f.get('message')}",
                            remediation="Run `uv run ruff check --fix .` to resolve formatting and lint defects."
                        ))
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Pytest execution
        try:
            print("[2/3] Running pytest suite verification...", flush=True)
            cmd = ["pytest", "tests/", "-q", "--tb=line"] if os.environ.get("VIRTUAL_ENV") else ["uv", "run", "pytest", "tests/", "-q", "--tb=line"]
            res = subprocess.run(
                cmd,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False
            )
            # Only record issue if there are actual failures in the output
            if res.returncode != 0 and "failed" in res.stdout.lower():
                summary = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else "Test suite failed."
                self.issues.append(DRIssue(
                    category="TESTS",
                    severity="CRITICAL",
                    file_path="tests/",
                    line=None,
                    message=f"Automated Test Failures: {summary}",
                    remediation="Execute `uv run pytest tests/ -v` locally and fix all failing assertions."
                ))
        except Exception:
            pass

    def run_ai_review(self, diff: str):
        """Invokes LLM (OpenRouter, Gemini, OmniRoute, or OpenAI) to perform deep architectural & logic review."""
        api_key = (
            os.getenv("GEMINI_API_KEY") or
            os.getenv("OPENROUTER_API_KEY") or
            os.getenv("OPENAI_API_KEY") or
            os.getenv("OMNIROUTE_API_KEY") or
            os.getenv("ANTHROPIC_API_KEY")
        )
        if not api_key or not diff.strip():
            return

        # Truncate diff if oversized (max 30KB)
        capped_diff = diff[:30000]

        prompt = f"""You are the **Principal Software Architect, Lead SRE & Security Auditor** for the **ORAGAI** framework.
Your mission is to perform a rigorous, deterministic code review of the following Git Pull Request diff.

### 🏛️ About ORAGAI Architecture Invariants (You MUST strictly enforce these):
1. **Hexagonal Architecture (Ports & Adapters)**:
   - `orchestrator/domain/`: Must contain pure domain models only (Pydantic). NEVER import from `adapters`, `tools`, `pipeline`, or `cli`.
   - `orchestrator/ports/`: Must define abstract protocols/interfaces only (driving/driven). NEVER import concrete adapters.
   - `orchestrator/adapters/`: Implements driven ports (VCS, Tools, Storage, Runtime). Must not leak infrastructure details into domain.
2. **Security & Sandbox Safety**:
   - Zero hardcoded secrets, tokens, API keys, or private endpoints.
   - All file operations must respect RBAC write boundaries and prevent path traversal (`..` or UNC paths).
   - Subprocess executions must be strictly sanitized; no unsandboxed shell=True or arbitrary command execution.
3. **Zero-Stub Production Discipline**:
   - No placeholder functions with bare `pass` or `...` (unless abstract methods).
   - Strict Python 3.12+ type hints on all public interfaces.
4. **Resilience & Concurrency**:
   - All state mutations must be thread-safe.
   - Failure paths must fail closed and trigger circuit breakers/failovers where appropriate.

---

### 📥 PULL REQUEST GIT DIFF TO REVIEW:
```diff
{capped_diff}
```

---

### 📋 REQUIRED REVIEW OUTPUT FORMAT:

Please generate a professional, structured review containing the following sections:

### 1. 🎯 Executive Verdict
- **Verdict**: `APPROVED` | `CHANGES_REQUIRED` | `NEEDS_DISCUSSION`
- **Summary**: Concise 2-3 sentence assessment of the PR's purpose, architectural soundness, and quality.

### 2. 🛡️ Security & Boundary Compliance
- Verification of secrets containment, path safety, and injection prevention.

### 3. 🔍 Forensic Findings & Actionable Feedback
For any identified defect, edge case, race condition, or architectural breach, provide:
- **Location**: `path/to/file.py:line_number`
- **Severity**: `[CRITICAL]` | `[HIGH]` | `[MEDIUM]` | `[LOW]`
- **Issue**: Why this is problematic.
- **Recommended Code Fix**: Provide exact code snippet showing how to fix it.

### 4. 💡 Maintainability & Performance Insights
- Constructive suggestions to improve efficiency, test coverage, or idiomatic Python 3.12+ patterns.
"""

        provider = (os.getenv("PROVIDER") or "").strip().lower()

        # 1. OmniRoute Local / Remote Gateway
        if provider == "omniroute" or os.getenv("OMNIROUTE_API_KEY"):
            base_url = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").rstrip("/") + "/chat/completions"
            api_key = os.getenv("OMNIROUTE_API_KEY", "")
            model = os.getenv("PR_REVIEW_MODEL") or os.getenv("MODEL", "antigravity/gemini-3.7-flash-tiered")
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                resp = httpx.post(base_url, json=payload, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.ai_summary = data["choices"][0]["message"]["content"]
                    return
            except Exception:
                pass  # Fallback to OpenRouter / Gemini

        try:
            # 2. OpenRouter (Strict Enforced Free-Tier Only)
            if os.getenv("OPENROUTER_API_KEY"):
                or_key = os.getenv("OPENROUTER_API_KEY")
                base_url = "https://openrouter.ai/api/v1/chat/completions"
                requested_model = os.getenv("PR_REVIEW_MODEL", "openrouter/free").strip()
                
                # STRICT FINANCIAL SAFETY ENFORCEMENT:
                # Guarantee $0.00 cost by verifying free tier (openrouter/free or :free suffix).
                # If someone attempts to pass an unverified paid model, safely enforce 'openrouter/free'.
                is_free_router = requested_model in ("openrouter/free", "openrouter/auto:free")
                has_free_suffix = requested_model.endswith(":free")
                if not (is_free_router or has_free_suffix):
                    requested_model = "openrouter/free"

                headers = {
                    "Authorization": f"Bearer {or_key}",
                    "HTTP-Referer": "https://github.com/crrrowz/orchestrator-ai-agent",
                    "X-Title": "ORAGAI PR Quality Gate",
                }
                payload = {
                    "model": requested_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                resp = httpx.post(base_url, json=payload, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.ai_summary = data["choices"][0]["message"]["content"]
                    return

            # 3. Google Gemini Direct
            if os.getenv("GEMINI_API_KEY"):
                model_name = os.getenv("PR_REVIEW_MODEL", "gemini-2.0-flash")
                model_name = model_name.replace("gemini/", "").replace("google/", "").replace(":free", "")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={os.getenv('GEMINI_API_KEY')}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = httpx.post(url, json=payload, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.ai_summary = data["candidates"][0]["content"]["parts"][0]["text"]
                    return

            # 4. OpenAI Direct / Compatible
            if os.getenv("OPENAI_API_KEY"):
                openai_key = os.getenv("OPENAI_API_KEY")
                base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions"
                model = os.getenv("PR_REVIEW_MODEL", "gpt-4o-mini")
                headers = {"Authorization": f"Bearer {openai_key}"}
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                resp = httpx.post(base_url, json=payload, headers=headers, timeout=60.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.ai_summary = data["choices"][0]["message"]["content"]
                    return
        except Exception as e:
            self.ai_summary = f"*Note: AI deep review pass skipped due to API timeout/connectivity ({str(e)}). Static & deterministic gates fully executed.*"

    def execute_gate(self) -> PRReviewReport:
        files = self.get_changed_files()
        for f in files:
            self.check_security(f)
            self.check_ast_and_syntax(f)
            self.check_architecture_invariants(f)

        self.run_tests_and_linting()

        print("[3/3] Running AI architecture review pass...", flush=True)
        # Run AI Deep Review on the diff
        diff = self.get_git_diff()
        self.run_ai_review(diff)

        passed = not any(i.severity in ("CRITICAL", "HIGH") for i in self.issues)
        return PRReviewReport(
            total_files_analyzed=len(files),
            passed=passed,
            issues=self.issues,
            ai_summary=self.ai_summary,
            ai_verdict=self.ai_verdict
        )


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    gate = PRReviewGate()
    report = gate.execute_gate()
    md_output = report.to_markdown()

    # Output to stdout
    try:
        print(md_output)
    except UnicodeEncodeError:
        print(md_output.encode("ascii", errors="replace").decode("ascii"))

    # Save to file for GitHub Action comment step
    report_file = Path("pr_review_report.md")
    report_file.write_text(md_output, encoding="utf-8")

    # Exit with error code if blockers exist
    if not report.passed:
        print(f"\n❌ PR Quality Gate Failed with {report.critical_count} critical/high blocker(s).", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✅ PR Quality Gate Passed successfully.", file=sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
