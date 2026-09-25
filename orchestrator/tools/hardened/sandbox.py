"""Subprocess Isolation, Job Group Timeout Management, and Terminal Sandbox.

Executes grammar-validated commands in an isolated environment with UTF-8
standard streams and deterministic timeout killers.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

from orchestrator.tools.hardened.grammar import CommandGrammarValidator
from orchestrator.tools.hardened.models import (
    TerminalActionRequest,
    TerminalObservationResult,
)
from orchestrator.tools.hardened.security import (
    SENSITIVE_ENV_KEYWORDS,
    sanitize_text_secrets,
)


class TerminalSandboxEngine:
    """Isolated execution engine managing subprocess lifecycles, environments, and timeouts."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def build_sanitized_environment(self) -> Dict[str, str]:
        """Construct sanitized process environment isolating child from host secrets."""
        allowed_system_vars = {
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "PATH",
            "WINDIR",
            "TMP",
            "TEMP",
            "USERPROFILE",
            "HOME",
            "LANG",
            "TERM",
            "COMSPEC",
            "PATHEXT",
            "APPDATA",
            "LOCALAPPDATA",
            "PROGRAMDATA",
            "ALLUSERSPROFILE",
            "NUMBER_OF_PROCESSORS",
            "PROCESSOR_ARCHITECTURE",
            "OS",
        }

        env: Dict[str, str] = {}
        for k, v in os.environ.items():
            k_upper = k.upper()
            if any(sk in k_upper for sk in SENSITIVE_ENV_KEYWORDS):
                continue
            if k_upper in allowed_system_vars:
                env[k] = v

        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["LC_ALL"] = "C.UTF-8"
        env["WORKSPACE_PATH"] = str(self.workspace_root)

        # Prepend workspace .venv
        is_windows = sys.platform == "win32" or os.name == "nt"
        venv_dir = self.workspace_root / ".venv" / ("Scripts" if is_windows else "bin")
        if venv_dir.exists():
            existing_path = env.get("PATH", "")
            env["PATH"] = (
                f"{str(venv_dir)}{os.pathsep}{existing_path}"
                if existing_path
                else str(venv_dir)
            )
            env["VIRTUAL_ENV"] = str(self.workspace_root / ".venv")

        existing_py_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{str(self.workspace_root)}{os.pathsep}{existing_py_path}"
            if existing_py_path
            else str(self.workspace_root)
        )

        return env

    @classmethod
    def _kill_process_tree(cls, pid: int) -> None:
        """Clean tree-kill on hung child processes across Windows NT and POSIX."""
        if not pid:
            return
        is_windows = sys.platform == "win32" or os.name == "nt"
        if is_windows:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass
        else:
            try:
                import signal

                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                try:
                    os.kill(pid, 9)
                except Exception:
                    pass

    def execute(
        self, action: TerminalActionRequest, base_dir: Optional[Path] = None
    ) -> TerminalObservationResult:
        """Execute validated command within workspace sandbox with hard timeout killer."""
        target_root = (base_dir or self.workspace_root).resolve()
        target_root.mkdir(parents=True, exist_ok=True)

        # 1. Translate command for platform if translator is available
        clean_cmd = (action.command or "").strip()
        is_windows = sys.platform == "win32" or os.name == "nt"

        try:
            from orchestrator.sentinel.command_interceptor import (
                TerminalCommandTranslator,
            )

            is_trans, trans_cmd, _ = TerminalCommandTranslator.intercept_and_translate(
                clean_cmd
            )
            if is_trans:
                clean_cmd = trans_cmd
        except Exception:
            pass

        # 2. Grammar validation
        validation = CommandGrammarValidator.validate_command(clean_cmd)
        if not validation.is_valid:
            err_msg = validation.rejection_reason or "Command validation rejected."
            return TerminalObservationResult(
                exit_code=126,
                stdout="",
                stderr=err_msg,
                is_error=True,
                steering_directive=f"Command rejected by sandbox security policy: {err_msg}",
            )

        env = self.build_sanitized_environment()

        # 3. Assemble execution arguments
        if validation.is_powershell_pipeline and is_windows:
            exec_args = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                clean_cmd,
            ]
        elif validation.executable_path in ("pytest", "ruff", "mypy"):
            exec_args = [
                sys.executable,
                "-m",
                validation.executable_path,
                *validation.command_line_args,
            ]
        elif (
            validation.executable_path in ("dir", "type", "cls", "copy", "del", "move")
            and is_windows
        ):
            exec_args = ["cmd.exe", "/c", clean_cmd]
        elif validation.executable_path in ("python", "py"):
            exec_args = [sys.executable, *validation.command_line_args]
        else:
            resolved_bin = (
                shutil.which(validation.executable_path, path=env.get("PATH"))
                or validation.executable_path
            )
            exec_args = [resolved_bin, *validation.command_line_args]

        timeout_sec = (
            action.timeout_seconds
            if (action.timeout_seconds and action.timeout_seconds > 0)
            else 60
        )
        proc = None
        try:
            proc = subprocess.Popen(
                exec_args,
                cwd=str(target_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                shell=False,
            )
            stdout_raw, stderr_raw = proc.communicate(timeout=timeout_sec)
            stdout_clean = sanitize_text_secrets(stdout_raw or "")
            stderr_clean = sanitize_text_secrets(stderr_raw or "")

            return TerminalObservationResult(
                exit_code=proc.returncode,
                stdout=stdout_clean,
                stderr=stderr_clean,
                timed_out=False,
                is_error=(proc.returncode != 0),
            )

        except subprocess.TimeoutExpired:
            if proc:
                self._kill_process_tree(proc.pid)
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    stdout_raw, stderr_raw = proc.communicate(timeout=2)
                except Exception:
                    stdout_raw, stderr_raw = "", ""
            else:
                stdout_raw, stderr_raw = "", ""

            stdout_clean = sanitize_text_secrets(stdout_raw or "")
            stderr_clean = sanitize_text_secrets(stderr_raw or "")
            timeout_msg = f"Command timed out after {timeout_sec} seconds."
            return TerminalObservationResult(
                exit_code=-1,
                stdout=stdout_clean,
                stderr=f"{timeout_msg}\n{stderr_clean}".strip(),
                timed_out=True,
                is_error=True,
                steering_directive="Execution timed out. Narrow test target (-k <name>) or increase timeout_seconds.",
            )
        except Exception as e:
            if proc:
                try:
                    self._kill_process_tree(proc.pid)
                except Exception:
                    pass
            return TerminalObservationResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution Subprocess Exception: {str(e)}",
                is_error=True,
            )
