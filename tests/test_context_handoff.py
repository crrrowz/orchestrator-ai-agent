"""Comprehensive Unit and Integration Tests for Context & Evidence Handoff Mesh (P6).

File Location: tests/test_context_handoff.py
Plan Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md Section 7
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.context.handoff import (
    ArchitectHandoffPayload,
    CompactedFrame,
    ContextBlock,
    ContextHeadroomExhaustionError,
    ContextSynthesizer,
    ContextTier,
    ContextTierEnum,
    CrossAgentContextManager,
    CrossAgentHandoffPayload,
    DeveloperHandoffPayload,
    DiagnosticCompactor,
    DiagnosticFailureTrace,
    DiagnosticTraceCompactor,
    DiagnosticTraceSummary,
    FreshnessState,
    FreshnessValidator,
    HandoffEnvelope,
    HandoffIntegrityError,
    HandoffType,
    HandoffTypeEnum,
    LineAnchoredFix,
    MissingHandoffArtifactError,
    PersonaViewType,
    RequiredSymbolSpec,
    ReviewerHandoffPayload,
    SubjectFingerprint,
    TesterHandoffPayload,
    WorkspaceDigest,
)


# ============================================================================
# P6-T01: TIER 0 IMMUTABILITY & HEADROOM EXHAUSTION
# ============================================================================

def test_tier0_intent_never_truncated_under_budget_cap():
    """Tier 0 Intent elements must never be sliced, truncated, or dropped."""
    synthesizer = ContextSynthesizer(max_context_tokens=10_000, reserve_headroom_tokens=2_000)

    # 10 critical acceptance criteria
    ac_list = [f"AC_{i:02d}: Given condition {i}, when action {i} executes, then result {i} must hold." for i in range(10)]
    t0_blocks = [
        ContextBlock(ContextTierEnum.TIER_0_INTENT, "Core Task Requirements", "Must build secure JWT auth service."),
        ContextBlock(ContextTierEnum.TIER_0_INTENT, "Acceptance Criteria", "\n".join(ac_list)),
    ]

    # Large Tier 2 and Tier 3 blocks that would otherwise cause token crunch
    t2_blocks = [
        ContextBlock(ContextTierEnum.TIER_2_CODE, f"Module_{i}", "x = 1\n" * 500)
        for i in range(5)
    ]
    t3_blocks = [
        ContextBlock(ContextTierEnum.TIER_3_ARCHITECTURE, "Topology", "node -> node\n" * 300)
    ]

    prompt = synthesizer.assemble_prompt(
        view_type=PersonaViewType.DEVELOPER_VIEW,
        tier0_intent_blocks=t0_blocks,
        tier1_diagnostic_blocks=[],
        tier2_code_blocks=t2_blocks,
        tier3_architecture_blocks=t3_blocks,
    )

    # 100% of Acceptance Criteria must be preserved intact
    for ac in ac_list:
        assert ac in prompt, f"Expected critical AC to be preserved: {ac}"
    assert "Must build secure JWT auth service." in prompt


def test_tier0_intent_raises_headroom_exhaustion_when_oversized():
    """When Tier 0 intent exceeds safe budget limit (40% ceiling), raise fatal exception."""
    synthesizer = ContextSynthesizer(max_context_tokens=1000, reserve_headroom_tokens=200)
    # Ceiling is 800 tokens. 40% is 320 tokens (~1280 chars)
    giant_intent = "CRITICAL SPECIFICATION REQUIREMENT\n" * 100

    t0_blocks = [
        ContextBlock(ContextTierEnum.TIER_0_INTENT, "Giant Requirements", giant_intent)
    ]

    with pytest.raises(ContextHeadroomExhaustionError) as exc_info:
        synthesizer.assemble_prompt(
            view_type=PersonaViewType.DEVELOPER_VIEW,
            tier0_intent_blocks=t0_blocks,
            tier1_diagnostic_blocks=[],
            tier2_code_blocks=[],
            tier3_architecture_blocks=[],
        )
    assert "Tier 0 intent exceeds safe budget limit" in str(exc_info.value)


# ============================================================================
# P6-T02: OUTPUT HEADROOM RESERVE GUARANTEE
# ============================================================================

def test_output_headroom_reserve_guarantee():
    """Context synthesizer strictly maintains reserved generation headroom H_reserve."""
    max_tokens = 4_000
    reserve_tokens = 1_000  # >= 2048 or 15%
    synthesizer = ContextSynthesizer(max_context_tokens=max_tokens, reserve_headroom_tokens=reserve_tokens)

    # Target ceiling is max_tokens - reserve_tokens = 3,000 tokens
    assert synthesizer.target_prompt_ceiling_tokens == 3_000

    # Inject large content in Tier 1, Tier 2, Tier 3
    t0_blocks = [ContextBlock(ContextTierEnum.TIER_0_INTENT, "Task", "Short task description")]
    t1_blocks = [ContextBlock(ContextTierEnum.TIER_1_DIAGNOSTICS, "Trace", "trace error line\n" * 400)]
    t2_blocks = [ContextBlock(ContextTierEnum.TIER_2_CODE, "Code", "def foo():\n    return 42\n" * 800)]
    t3_blocks = [ContextBlock(ContextTierEnum.TIER_3_ARCHITECTURE, "Arch", "Graph node\n" * 800)]

    prompt = synthesizer.assemble_prompt(
        view_type=PersonaViewType.DEVELOPER_VIEW,
        tier0_intent_blocks=t0_blocks,
        tier1_diagnostic_blocks=t1_blocks,
        tier2_code_blocks=t2_blocks,
        tier3_architecture_blocks=t3_blocks,
    )

    estimated_prompt_tokens = len(prompt) / 4.0
    # Prompt must never eat into reserved output headroom
    assert estimated_prompt_tokens <= synthesizer.target_prompt_ceiling_tokens + 50


# ============================================================================
# P6-T03: DIAGNOSTIC TRACE COMPACTION
# ============================================================================

def test_diagnostic_compactor_extracts_failing_frame():
    """Diagnostic compactor strips ANSI sequences, passing noise, and extracts leaf failure frame."""
    raw_pytest_output = """
[1m============================= test session starts =============================[0m
platform win32 -- Python 3.12.11, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\\workspace
collected 4 items

tests/test_auth.py [32m.[0m[32m.[0m[31mF[0m[32m.[0m                                                  [31m[100%][0m

================================== FAILURES ===================================
[31m[1m_____________________________ test_jwt_expiration _____________________________[0m

    def test_jwt_expiration():
        token = create_jwt(expires_in=-10)
>       assert token.is_valid() is True
[1m[31mE       AssertionError: assert False is True[0m
[1m[31mE        +  where False = is_valid()[0m

tests/test_auth.py:42: in test_jwt_expiration
    assert token.is_valid() is True
=========================== short test summary info ===========================
FAILED tests/test_auth.py::test_jwt_expiration - AssertionError: assert False is True
========================= 1 failed, 3 passed in 0.12s =========================
"""
    summary = DiagnosticTraceCompactor.compact_pytest_output(raw_pytest_output, exit_code=1)

    assert summary.total_failures == 1
    assert len(summary.traces) == 1
    trace = summary.traces[0]
    assert trace.node_id == "test_jwt_expiration"
    assert trace.exception_type == "AssertionError"
    assert "False is True" in trace.exception_message

    assert trace.primary_frame is not None
    assert "test_auth.py" in trace.primary_frame.file_path
    assert trace.primary_frame.line_number == 42

    md = trace.to_markdown()
    # High-signal and concise:
    assert "**FAILED TEST:** `test_jwt_expiration`" in md
    assert "- **Location:** `tests/test_auth.py:42`" in md
    assert "\x1B" not in md  # Zero ANSI escape codes
    assert len(md) < 800  # Well within the 800-char compact budget


def test_diagnostic_compactor_syntax_error():
    """Diagnostic compactor parses Python syntax compilation errors."""
    syntax_stderr = """
  File "orchestrator/auth/jwt.py", line 18
    def broken_func(
                    ^
SyntaxError: '(' was never closed
"""
    trace = DiagnosticTraceCompactor.compact_syntax_error(syntax_stderr)
    assert trace.node_id == "compilation_syntax_error"
    assert trace.exception_type == "SyntaxError"
    assert "was never closed" in trace.exception_message
    assert trace.primary_frame is not None
    assert trace.primary_frame.line_number == 18
    assert "jwt.py" in trace.primary_frame.file_path


# ============================================================================
# P6-T04: CRYPTOGRAPHIC ENVELOPE SEALING & INTEGRITY
# ============================================================================

def test_handoff_envelope_cryptographic_sealing():
    """HandoffEnvelope calculates deterministic SHA-256 digest and catches tampering."""
    payload_data = {
        "milestone_id": "M1_DATA_MODEL",
        "target_files": ["src/models.py"],
        "target_symbols": ["UserSession", "create_session"],
    }
    envelope = HandoffEnvelope(
        handoff_type=HandoffTypeEnum.ARCHITECT_TO_DEVELOPER,
        sender_persona="Architect",
        recipient_persona="Developer",
        milestone_id="M1_DATA_MODEL",
        typed_payload=payload_data,
    )
    mock_ws_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    envelope.seal(mock_ws_hash)

    assert envelope.workspace_sha256 == mock_ws_hash
    assert envelope.payload_sha256 != ""
    assert envelope.verify_integrity() is True

    # Tamper with payload
    envelope.typed_payload["target_files"].append("src/tampered.py")
    assert envelope.verify_integrity() is False


def test_cross_agent_handoff_payload_sealing():
    """CrossAgentHandoffPayload computes SHA-256 digest and verifies integrity."""
    payload = CrossAgentHandoffPayload(
        handoff_type=HandoffTypeEnum.DEVELOPER_TO_TESTER,
        milestone_id="M1_CORE",
        source_role="Developer",
        target_role="Tester",
        target_files=["src/auth.py"],
        required_symbols=[
            RequiredSymbolSpec(name="login", type="function", docstring="Authenticates user.")
        ],
        required_fixes=[
            LineAnchoredFix(file="src/auth.py", line=45, symbol="login", issue="None check missing", remediation="Add guard")
        ],
    )
    payload.seal("ws_hash_12345")
    assert payload.payload_hash != ""
    assert payload.verify_integrity() is True

    # Alter fix
    payload.required_fixes[0].line = 99
    assert payload.verify_integrity() is False


# ============================================================================
# P6-T05: WORKSPACE DIGEST & FINGERPRINTING
# ============================================================================

def test_workspace_digest_detects_file_modification(tmp_path: Path):
    """Mutating a workspace file immediately alters the composite SHA-256 digest."""
    file_a = tmp_path / "service.py"
    file_b = tmp_path / "utils.py"

    file_a.write_text("def run(): pass\n", encoding="utf-8")
    file_b.write_text("def helper(): return 1\n", encoding="utf-8")

    digest1 = FreshnessValidator.create_workspace_digest(tmp_path)
    assert len(digest1.file_digests) == 2
    assert "service.py" in digest1.file_digests
    assert "utils.py" in digest1.file_digests

    # Modify file_a
    file_a.write_text("def run(): return 'modified'\n", encoding="utf-8")
    digest2 = FreshnessValidator.create_workspace_digest(tmp_path)

    assert digest2.composite_sha256 != digest1.composite_sha256
    modified = FreshnessValidator.detect_modified_files(digest1, digest2)
    assert modified == {"service.py"}


# ============================================================================
# P6-T06 & P6-T07: FRESHNESS VALIDATION & ISOLATED PROOF PRESERVATION
# ============================================================================

def test_freshness_validator_invalidates_stale_proof(tmp_path: Path):
    """Modifying a target file invalidates dependent evidence (transitions to STALE)."""
    target = tmp_path / "auth.py"
    target.write_text("class Authenticator: pass\n", encoding="utf-8")

    digest_at_evidence = FreshnessValidator.create_workspace_digest(tmp_path)
    evidence_hash = digest_at_evidence.composite_sha256

    # Verify baseline is FRESH
    state, msg = FreshnessValidator.evaluate_evidence_freshness(
        evidence_workspace_sha256=evidence_hash,
        current_workspace_digest=digest_at_evidence,
        target_files=["auth.py"],
    )
    assert state == FreshnessState.FRESH

    # Developer edits auth.py
    target.write_text("class Authenticator:\n    def login(self): return True\n", encoding="utf-8")
    current_digest = FreshnessValidator.create_workspace_digest(tmp_path)

    state, msg = FreshnessValidator.evaluate_evidence_freshness(
        evidence_workspace_sha256=evidence_hash,
        current_workspace_digest=current_digest,
        target_files=["auth.py"],
    )
    assert state == FreshnessState.STALE
    assert "auth.py" in msg


def test_freshness_validator_preserves_isolated_proof(tmp_path: Path):
    """Modifying an unrelated file preserves evidence for untouched target modules."""
    module_a = tmp_path / "module_a.py"
    module_b = tmp_path / "module_b.py"

    module_a.write_text("def func_a(): return 1\n", encoding="utf-8")
    module_b.write_text("def func_b(): return 2\n", encoding="utf-8")

    digest_at_evidence = FreshnessValidator.create_workspace_digest(tmp_path)
    evidence_hash_for_a = digest_at_evidence.composite_sha256

    # Now edit module_b only
    module_b.write_text("def func_b(): return 999\n", encoding="utf-8")
    current_digest = FreshnessValidator.create_workspace_digest(tmp_path)

    # Invalidate cascade check with explicit target
    cascade = FreshnessValidator.cascade_invalidation(
        modified_files={"module_b.py"},
        milestone_targets={
            "M1_MODULE_A": ["module_a.py"],
            "M2_MODULE_B": ["module_b.py"],
        },
    )
    assert cascade["M1_MODULE_A"] == FreshnessState.FRESH
    assert cascade["M2_MODULE_B"] == FreshnessState.STALE


# ============================================================================
# P6-T08: ELIMINATION OF RAW FALLBACKS (MANDATORY HANDOFF ENFORCEMENT)
# ============================================================================

def test_missing_handoff_triggers_fatal_error(tmp_path: Path):
    """Missing upstream handoff halts execution with MissingHandoffArtifactError instead of falling back to raw tasks."""
    manager = CrossAgentContextManager(workspace_path=tmp_path)

    with pytest.raises(MissingHandoffArtifactError) as exc_info:
        manager.validate_required_handoff(
            handoff_type=HandoffTypeEnum.ARCHITECT_TO_DEVELOPER,
            milestone_id="M1_DATA_MODEL",
        )
    assert "Falling back to unguided raw tasks is prohibited" in str(exc_info.value)


# ============================================================================
# P6-T09: PERSONA VIEW ISOLATION & FILTERING
# ============================================================================

def test_persona_view_isolation_and_filtering():
    """ContextSynthesizer outputs tailored, role-specific views without leaking unneeded context."""
    synthesizer = ContextSynthesizer(max_context_tokens=10_000)

    # 1. Architect View: gets skeleton, NO granular code diffs
    arch_view = synthesizer.build_architect_view(
        task_description="Build distributed KV store",
        acceptance_criteria=["AC1: Put/Get operations", "AC2: Raft consensus"],
        architecture_skeleton="src/storage -> src/consensus",
        skills=["Skill: Senior Architect Protocol"],
    )
    assert "# ORAGAI Multi-Agent Execution Frame: `ARCHITECT_VIEW`" in arch_view
    assert "Build distributed KV store" in arch_view
    assert "src/storage -> src/consensus" in arch_view
    assert "Senior Architect Protocol" in arch_view
    assert "Developer AST Implementation Diffs" not in arch_view

    # 2. Reviewer View: gets unified diff, acceptance criteria, invariants
    rev_view = synthesizer.build_reviewer_view(
        milestone_id="M1_RAFT",
        git_diff_md="+ def append_entries(): pass",
        acceptance_criteria_md="- AC2: Raft consensus verified",
        test_execution_summary="3 passed in 0.05s",
        preflight_report_md="PreFlight: CLEAN",
        architectural_invariants_md="Invariants: Zero Stubs",
        skills=["Skill: Reviewer Standards"],
    )
    assert "# ORAGAI Multi-Agent Execution Frame: `REVIEWER_VIEW`" in rev_view
    assert "Complete Multi-File Unified Git Diff (Untruncated)" in rev_view
    assert "+ def append_entries(): pass" in rev_view
    assert "Reviewer Standards" in rev_view


# ============================================================================
# P6-T10: UNTRUNCATED MULTI-FILE DIFF FOR REVIEWER
# ============================================================================

def test_untruncated_diff_rendering_for_reviewer():
    """Multi-file diffs exceeding legacy 4,000 characters are untruncated for Reviewer."""
    synthesizer = ContextSynthesizer(max_context_tokens=32_000)

    # Generate a realistic 8,000 character diff (2x legacy cap)
    diff_lines = []
    for f_idx in range(5):
        diff_lines.append(f"diff --git a/src/service_{f_idx}.py b/src/service_{f_idx}.py")
        diff_lines.append("--- a/src/service_{f_idx}.py\n+++ b/src/service_{f_idx}.py")
        for line_idx in range(30):
            diff_lines.append(f"+    def process_item_{line_idx}(data: dict) -> bool:")
            diff_lines.append(f"+        return validate(data, index={line_idx})")
    large_diff = "\n".join(diff_lines)
    assert len(large_diff) > 6000

    view = synthesizer.build_reviewer_view(
        milestone_id="M1_SERVICES",
        git_diff_md=large_diff,
        acceptance_criteria_md="All 5 services validate items",
        test_execution_summary="15 tests passed",
        preflight_report_md="CLEAN",
        architectural_invariants_md="No stubs",
    )
    # The entire diff must be present without truncation marks
    assert "... [diff truncated]" not in view
    assert "process_item_29" in view


# ============================================================================
# P6-T11: AST CODE FOLDING IN TIER 2 UNDER TOKEN PRESSURE
# ============================================================================

def test_ast_folding_in_tier2_under_constrained_budget():
    """Developer view automatically applies AST folding to large files preserving target symbols."""
    synthesizer = ContextSynthesizer(max_context_tokens=20_000)

    code = """
class LargeRepository:
    def target_method(self, user_id: str) -> bool:
        if not user_id:
            return False
        return True

    def non_target_helper_one(self, data: dict) -> None:
        '''Helper one docstring.'''
        line1 = data.get("a")
        line2 = data.get("b")
        line3 = data.get("c")
        line4 = data.get("d")
        line5 = data.get("e")
        line6 = data.get("f")
        return None

    def non_target_helper_two(self, config: dict) -> int:
        '''Helper two docstring.'''
        val1 = config.get("timeout", 10)
        val2 = config.get("retries", 3)
        val3 = config.get("backoff", 1)
        val4 = config.get("factor", 2)
        val5 = config.get("jitter", 0.1)
        val6 = config.get("seed", 42)
        return val1 * val2
"""
    # Pad code to >2000 chars to trigger AST folding branch in build_developer_view
    padded_code = code + "\n# Extra padding\n" * 100

    view = synthesizer.build_developer_view(
        milestone_id="M1_REPO",
        requirements_md="Implement target_method",
        acceptance_criteria_md="AC1: target_method handles empty user_id",
        upstream_architect_envelope=None,
        target_code_map={"src/repo.py": padded_code},
        target_symbols={"target_method"},
    )

    # Target symbol method body must remain intact
    assert "def target_method(self, user_id: str) -> bool:" in view
    assert "if not user_id:" in view

    # Non-target methods with > 5 lines must be folded
    assert "Folded implementation" in view
    assert "Helper one docstring." in view


# ============================================================================
# P6-T12: CROSS-AGENT CONTEXT MANAGER FACADE INTEGRATION
# ============================================================================

def test_cross_agent_context_manager_facade_integration(tmp_path: Path):
    """Test end-to-end CrossAgentContextManager orchestrating sealing, freshness, and views."""
    # 1. Setup workspace
    auth_file = tmp_path / "auth.py"
    auth_file.write_text("def login(): pass\n", encoding="utf-8")

    manager = CrossAgentContextManager(workspace_path=tmp_path)

    # 2. Record Architect Handoff
    arch_payload = ArchitectHandoffPayload(
        milestone_id="M1_AUTH",
        target_files=["auth.py"],
        target_symbols=["login"],
        acceptance_criteria=[{"id": "AC1", "spec": "Valid credentials return token"}],
        architectural_boundaries=["No raw SQL"],
        implementation_guidance="Use bcrypt for passwords",
    )
    arch_envelope = HandoffEnvelope(
        handoff_type=HandoffTypeEnum.ARCHITECT_TO_DEVELOPER,
        sender_persona="Architect",
        recipient_persona="Developer",
        milestone_id="M1_AUTH",
        typed_payload=arch_payload.to_dict(),
    )
    sealed_arch = manager.record_handoff(arch_envelope)
    assert sealed_arch.payload_sha256 != ""

    # 3. Retrieve and validate
    retrieved = manager.validate_required_handoff(HandoffTypeEnum.ARCHITECT_TO_DEVELOPER, "M1_AUTH")
    assert retrieved.envelope_id == sealed_arch.envelope_id

    # 4. Generate Developer Prompt
    dev_prompt = manager.build_developer_prompt(
        milestone_id="M1_AUTH",
        requirements_md="Implement login authentication",
        acceptance_criteria_md="AC1: Valid credentials return token",
        upstream_architect_envelope=retrieved,
        target_code_map={"auth.py": "def login(): pass\n"},
        target_symbols={"login"},
    )
    assert "Active Milestone Slice" in dev_prompt
    assert "Upstream Architect Blueprint" in dev_prompt
    assert "auth.py" in dev_prompt

    # 5. Developer modifies code
    auth_file.write_text("def login(user, pwd): return True\n", encoding="utf-8")

    # 6. Freshness check shows STALE for previous evidence captured at t0
    state, msg = manager.evaluate_evidence_freshness(
        evidence_workspace_sha256=sealed_arch.workspace_sha256,
        target_files=["auth.py"],
    )
    assert state == FreshnessState.STALE

    # 7. Tester records verified test output
    raw_test_out = "FAILED tests/test_login.py::test_bad_pwd\nAssertionError: Expected False"
    trace_summary = manager.compact_test_output(raw_test_out, exit_code=1)
    assert trace_summary.total_failures == 1
