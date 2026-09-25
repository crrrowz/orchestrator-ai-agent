"""Canonical Context Synthesizer Engine for Dynamic Token Budgeting and Persona Prompt Views.

File Location: orchestrator/context/handoff/synthesizer.py
Architecture Reference: docs/plans/P6_CONTEXT_AND_EVIDENCE_HANDOFF_PLAN.md Section 2
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from orchestrator.context.handoff.models import (
    CHARS_PER_TOKEN_ESTIMATE,
    DEFAULT_MAX_CONTEXT_CHARS,
    DEFAULT_OUTPUT_HEADROOM_CHARS,
    DEFAULT_TOKEN_RESERVE_HEADROOM,
    ContextBlock,
    ContextHeadroomExhaustionError,
    ContextTierEnum,
    HandoffEnvelope,
    PersonaViewType,
)
from orchestrator.control.adaptive.clamper import ASTAwareContextClamper


class ContextSynthesizer:
    """Assembles mathematically bounded, persona-tailored, and priority-tiered prompts.

    Enforces the guaranteed output headroom formula:
        AvailableContextChars = MaxContextChars - OutputHeadroomChars
        C_target = C_max - H_reserve (where H_reserve >= 2,048 tokens / ~8,192 chars)

    Enforces the Context Monotonicity and Tier 0 Invariant:
        Tier 0 (Task Truth, Acceptance Criteria, RBAC, Invariants) is strictly immutable
        and never truncated. If Tier 0 exceeds safe allocation, raises ContextHeadroomExhaustionError.
        Pruning proceeds strictly in reverse priority order: Tier 3 -> Tier 2 -> Tier 1.
    """

    def __init__(
        self,
        max_context_tokens: int = 32_000,
        reserve_headroom_tokens: int = DEFAULT_TOKEN_RESERVE_HEADROOM,
        skills_root: Optional[Path] = None,
    ):
        self.max_context_tokens = max_context_tokens
        self.reserve_headroom_tokens = max(
            reserve_headroom_tokens,
            int(0.15 * max_context_tokens),
        )
        self.target_prompt_ceiling_tokens = self.max_context_tokens - self.reserve_headroom_tokens
        self.skills_root = skills_root or (Path(__file__).resolve().parents[3] / ".agents" / "skills")

    @property
    def max_context_chars(self) -> int:
        return int(self.max_context_tokens * CHARS_PER_TOKEN_ESTIMATE)

    @property
    def reserved_headroom_chars(self) -> int:
        return int(self.reserve_headroom_tokens * CHARS_PER_TOKEN_ESTIMATE)

    @property
    def target_prompt_ceiling_chars(self) -> int:
        return int(self.target_prompt_ceiling_tokens * CHARS_PER_TOKEN_ESTIMATE)

    def load_skills_for_role(self, role: str) -> List[str]:
        """Load skill instruction contents from .agents/skills/<role>/."""
        role_dir = self.skills_root / role.lower()
        if not role_dir.exists() or not role_dir.is_dir():
            return []

        skills_content: List[str] = []
        for skill_dir in sorted(role_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    skills_content.append(skill_md.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    continue
            else:
                rules_md = skill_dir / "rules.md"
                if rules_md.exists():
                    try:
                        skills_content.append(rules_md.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        continue
        return skills_content

    def assemble_prompt(
        self,
        view_type: PersonaViewType,
        tier0_intent_blocks: List[ContextBlock],
        tier1_diagnostic_blocks: List[ContextBlock],
        tier2_code_blocks: List[ContextBlock],
        tier3_architecture_blocks: List[ContextBlock],
    ) -> str:
        """Compose the complete prompt honoring priority tiers and headroom ceilings.

        Tier 0 is immutable. If Tier 0 exceeds 40% of target budget, raises
        ContextHeadroomExhaustionError rather than slicing critical requirements.
        """
        ceiling_tokens = self.target_prompt_ceiling_tokens

        # 1. Tier 0 Verification (Immutable Invariant)
        t0_tokens = sum(b.estimated_tokens for b in tier0_intent_blocks)
        if t0_tokens > int(0.40 * ceiling_tokens):
            raise ContextHeadroomExhaustionError(
                f"Tier 0 intent exceeds safe budget limit ({t0_tokens} tokens > 40% of {ceiling_tokens} tokens). "
                f"Slicing intent is prohibited by P6 invariant."
            )

        remaining_budget = ceiling_tokens - t0_tokens
        accepted_blocks: List[ContextBlock] = list(tier0_intent_blocks)

        # 2. Tier 1: Diagnostics & Upstream Handoffs (Cap: 30% of ceiling)
        t1_cap = int(0.30 * ceiling_tokens)
        t1_accepted = self._filter_blocks_to_budget(
            tier1_diagnostic_blocks, min(remaining_budget, t1_cap)
        )
        accepted_blocks.extend(t1_accepted)
        remaining_budget -= sum(b.estimated_tokens for b in t1_accepted)

        # 3. Tier 2: Code & Diffs (Cap: 35% of ceiling + absorbed remaining)
        t2_cap = int(0.35 * ceiling_tokens)
        t2_accepted = self._filter_blocks_to_budget(
            tier2_code_blocks, min(remaining_budget, t2_cap + max(0, remaining_budget - t2_cap))
        )
        accepted_blocks.extend(t2_accepted)
        remaining_budget -= sum(b.estimated_tokens for b in t2_accepted)

        # 4. Tier 3: Architecture Skeleton, Skills, & Memory (Elastic)
        if remaining_budget > 150:
            t3_accepted = self._filter_blocks_to_budget(
                tier3_architecture_blocks, remaining_budget
            )
            accepted_blocks.extend(t3_accepted)

        return self._render_markdown_prompt(view_type, accepted_blocks)

    def _filter_blocks_to_budget(
        self, blocks: List[ContextBlock], token_budget: int
    ) -> List[ContextBlock]:
        """Greedily accept blocks within token budget."""
        accepted: List[ContextBlock] = []
        spent = 0
        for block in blocks:
            if spent + block.estimated_tokens <= token_budget:
                accepted.append(block)
                spent += block.estimated_tokens
        return accepted

    def _render_markdown_prompt(
        self, view_type: PersonaViewType, blocks: List[ContextBlock]
    ) -> str:
        """Render ordered markdown prompt with system frame headers."""
        sections = [f"# ORAGAI Multi-Agent Execution Frame: `{view_type.value}`\n"]
        for block in blocks:
            sections.append(f"## {block.title}\n{block.content.strip()}\n")
        return "\n".join(sections)

    # ========================================================================
    # PERSONA-SPECIFIC PROMPT BUILDERS
    # ========================================================================

    def build_architect_view(
        self,
        task_description: str,
        acceptance_criteria: List[str],
        architecture_skeleton: str,
        public_api_contracts: Optional[List[Dict[str, Any]]] = None,
        skills: Optional[List[str]] = None,
    ) -> str:
        """Construct prompt view for Architect persona (Macro Planning & Milestone Formulation)."""
        t0_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Task Specification",
                f"### High-Level Objective:\n{task_description}",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Acceptance Criteria",
                "\n".join(f"- {ac}" for ac in acceptance_criteria) if acceptance_criteria else "No explicit criteria specified.",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Architect Persona Directives",
                "1. Role: Senior Systems Architect.\n"
                "2. Mission: Decompose task into formal MilestoneDAG, public API contracts, and explicit ACs.\n"
                "3. Sandboxing: Read-only analysis. Authoring of production source code is prohibited.\n"
                "4. Output Contract: Emit an ArchitectHandoffPayload with target files, symbols, and layering rules.",
            ),
        ]

        t1_blocks: List[ContextBlock] = []
        if public_api_contracts:
            t1_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_1_DIAGNOSTICS,
                    "Existing Public API Contracts",
                    json.dumps(public_api_contracts, indent=2),
                )
            )

        t2_blocks: List[ContextBlock] = []

        t3_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_3_ARCHITECTURE,
                "Codebase Architecture Skeleton",
                architecture_skeleton or "No repository topology provided.",
            )
        ]

        # Inject Architect skills
        loaded_skills = skills if skills is not None else self.load_skills_for_role("architect")
        for idx, skill_text in enumerate(loaded_skills, 1):
            t3_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_3_ARCHITECTURE,
                    f"Architect Operational Skill #{idx}",
                    skill_text,
                )
            )

        return self.assemble_prompt(
            PersonaViewType.ARCHITECT_VIEW,
            t0_blocks,
            t1_blocks,
            t2_blocks,
            t3_blocks,
        )

    def build_developer_view(
        self,
        milestone_id: str,
        requirements_md: str,
        acceptance_criteria_md: str,
        upstream_architect_envelope: Optional[HandoffEnvelope],
        target_code_map: Dict[str, str],
        target_symbols: Optional[Set[str]] = None,
        red_test_trace: Optional[str] = None,
        skills: Optional[List[str]] = None,
    ) -> str:
        """Construct prompt view for Developer persona (Micro-TDD Implementation)."""
        t0_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Active Milestone Slice",
                f"Target Milestone ID: `{milestone_id}`\n\n{requirements_md}",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Target Acceptance Criteria",
                acceptance_criteria_md,
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Developer Invariants & Anti-Stub Directives",
                "1. Zero Stubs: Prohibited from writing `pass`, `TODO`, `...`, or `raise NotImplementedError`.\n"
                "2. RBAC Sandbox: File edits strictly restricted to designated target files. Editing `tests/` is forbidden.\n"
                "3. Micro-TDD: Implement exact target symbols to satisfy red tests.\n"
                "4. Output Contract: Emit a DeveloperHandoffPayload with modified symbols and boundary hazards.",
            ),
        ]

        t1_blocks: List[ContextBlock] = []
        if upstream_architect_envelope:
            t1_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_1_DIAGNOSTICS,
                    "Upstream Architect Blueprint",
                    json.dumps(upstream_architect_envelope.typed_payload, indent=2),
                )
            )
        if red_test_trace:
            t1_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_1_DIAGNOSTICS,
                    "Failing Pytest Diagnostic Trace (Red Phase)",
                    red_test_trace,
                )
            )

        t2_blocks: List[ContextBlock] = []
        symbols = target_symbols or set()
        for file_path, code in target_code_map.items():
            # If code is large, apply AST folding for non-target symbols
            if len(code) > 2000:
                folded_code, was_folded = ASTAwareContextClamper.fold_python_source(
                    code, target_symbols=symbols
                )
                title = f"Source File: `{file_path}`" + (" (AST-Folded)" if was_folded else "")
                t2_blocks.append(
                    ContextBlock(ContextTierEnum.TIER_2_CODE, title, f"```python\n{folded_code}\n```")
                )
            else:
                t2_blocks.append(
                    ContextBlock(ContextTierEnum.TIER_2_CODE, f"Source File: `{file_path}`", f"```python\n{code}\n```")
                )

        t3_blocks: List[ContextBlock] = []
        loaded_skills = skills if skills is not None else self.load_skills_for_role("developer")
        for idx, skill_text in enumerate(loaded_skills, 1):
            t3_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_3_ARCHITECTURE,
                    f"Developer Engineering Skill #{idx}",
                    skill_text,
                )
            )

        return self.assemble_prompt(
            PersonaViewType.DEVELOPER_VIEW,
            t0_blocks,
            t1_blocks,
            t2_blocks,
            t3_blocks,
        )

    def build_tester_view(
        self,
        milestone_id: str,
        acceptance_criteria_md: str,
        developer_diff_md: str,
        modified_files: List[str],
        preflight_status_md: str,
        boundary_hazards: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
    ) -> str:
        """Construct prompt view for Tester persona (Negative Edge Case & Assertion Authoring)."""
        t0_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Verification Scope",
                f"Target Milestone ID: `{milestone_id}`\n- Modified Files: {', '.join(modified_files) if modified_files else 'None'}",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Acceptance Criteria Matrix",
                acceptance_criteria_md,
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Tester Directives & Sandboxing",
                "1. Role: Senior Test Engineer & QA Specialist.\n"
                "2. RBAC Sandbox: Authoring/editing restricted strictly to `tests/`. Modifying production source code is forbidden.\n"
                "3. Invariant: Author isolated unit tests probing both positive requirements and negative boundary hazards.\n"
                "4. Output Contract: Emit a TesterHandoffPayload with test execution node IDs and AC verification map.",
            ),
        ]

        t1_blocks: List[ContextBlock] = [
            ContextBlock(
                ContextTierEnum.TIER_1_DIAGNOSTICS,
                "PreFlight Compilation & Syntax Status",
                preflight_status_md or "PreFlight check: CLEAN",
            )
        ]
        if boundary_hazards:
            t1_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_1_DIAGNOSTICS,
                    "Identified Boundary Hazards to Probe",
                    "\n".join(f"- {h}" for h in boundary_hazards),
                )
            )

        t2_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_2_CODE,
                "Developer AST Implementation Diffs",
                f"```diff\n{developer_diff_md}\n```" if developer_diff_md else "No diff provided.",
            )
        ]

        t3_blocks: List[ContextBlock] = []
        loaded_skills = skills if skills is not None else self.load_skills_for_role("tester")
        for idx, skill_text in enumerate(loaded_skills, 1):
            t3_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_3_ARCHITECTURE,
                    f"Tester Rigorous Skill #{idx}",
                    skill_text,
                )
            )

        return self.assemble_prompt(
            PersonaViewType.TESTER_VIEW,
            t0_blocks,
            t1_blocks,
            t2_blocks,
            t3_blocks,
        )

    def build_reviewer_view(
        self,
        milestone_id: str,
        git_diff_md: str,
        acceptance_criteria_md: str,
        test_execution_summary: str,
        preflight_report_md: str,
        architectural_invariants_md: str,
        skills: Optional[List[str]] = None,
    ) -> str:
        """Construct prompt view for Reviewer persona (Independent Rubric Evaluation)."""
        t0_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Review Scope & Acceptance Criteria",
                f"Milestone ID: `{milestone_id}`\n\n### Acceptance Criteria:\n{acceptance_criteria_md}",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Inviolable Architectural & Security Invariants",
                architectural_invariants_md
                or "1. Zero Stubs: Prohibit pass/TODO/NotImplementedError.\n"
                "2. Zero Secrets: Prohibit hardcoded credentials or API keys.\n"
                "3. Clean Architecture: Respect module layering and boundaries.",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Reviewer Role Directives",
                "1. Role: Principal Code Reviewer & Security Auditor.\n"
                "2. RBAC Sandbox: Strictly read-only. File modifications are forbidden.\n"
                "3. Invariant: Provide binary verdict (APPROVED or REJECTED_WITH_DEFECTS).\n"
                "4. Output Contract: For defects, emit exact line-anchored LineAnchoredFix directives.",
            ),
        ]

        t1_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_1_DIAGNOSTICS,
                "Test Execution Proof & Coverage",
                test_execution_summary,
            ),
            ContextBlock(
                ContextTierEnum.TIER_1_DIAGNOSTICS,
                "PreFlight AST & Type-Check Verification",
                preflight_report_md or "PreFlight Report: CLEAN",
            ),
        ]

        t2_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_2_CODE,
                "Complete Multi-File Unified Git Diff (Untruncated)",
                f"```diff\n{git_diff_md}\n```",
            )
        ]

        t3_blocks: List[ContextBlock] = []
        loaded_skills = skills if skills is not None else self.load_skills_for_role("reviewer")
        for idx, skill_text in enumerate(loaded_skills, 1):
            t3_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_3_ARCHITECTURE,
                    f"Reviewer Standards Skill #{idx}",
                    skill_text,
                )
            )

        return self.assemble_prompt(
            PersonaViewType.REVIEWER_VIEW,
            t0_blocks,
            t1_blocks,
            t2_blocks,
            t3_blocks,
        )

    def build_remediation_view(
        self,
        milestone_id: str,
        defect_directives: List[Dict[str, Any]],
        failing_code_map: Dict[str, str],
        failing_assertion_trace: str,
        skills: Optional[List[str]] = None,
    ) -> str:
        """Construct prompt view for Remediation Specialist (Surgical Defect Repair)."""
        directives_formatted = []
        for d in defect_directives:
            fpath = d.get("file_path", d.get("file", "unknown"))
            line = d.get("line_anchor", d.get("line", 0))
            sym = d.get("symbol_name", d.get("symbol", ""))
            issue = d.get("violation_rule", d.get("issue", ""))
            expected = d.get("expected_behavior", d.get("remediation", ""))
            sev = d.get("severity", "MAJOR")
            directives_formatted.append(
                f"- **[{sev}]** `{fpath}:{line}` in `{sym}`:\n  * Issue: {issue}\n  * Required Fix: {expected}"
            )

        t0_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Remediation Mission & Budget Ceiling",
                f"Active Milestone: `{milestone_id}`\n"
                "Perform surgical, localized edits to resolve designated defect directives.\n"
                "Do NOT refactor unrelated modules or modify public API signatures.",
            ),
            ContextBlock(
                ContextTierEnum.TIER_0_INTENT,
                "Remediation Specialist Directives",
                "1. Role: Surgical Code Remediation Specialist.\n"
                "2. RBAC Sandbox: File edits restricted strictly to files named in defect directives.\n"
                "3. Invariant: Resolve all reviewer defect directives without introducing new regressions.\n"
                "4. Output Contract: Emit an updated DeveloperHandoffPayload with repaired symbols.",
            ),
        ]

        t1_blocks = [
            ContextBlock(
                ContextTierEnum.TIER_1_DIAGNOSTICS,
                "Reviewer Defect Directives",
                "\n".join(directives_formatted) if directives_formatted else "No explicit defect directives.",
            )
        ]
        if failing_assertion_trace:
            t1_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_1_DIAGNOSTICS,
                    "Failing Test Assertion Trace",
                    failing_assertion_trace,
                )
            )

        t2_blocks = []
        for fpath, code in failing_code_map.items():
            t2_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_2_CODE,
                    f"Source File Requiring Remediation: `{fpath}`",
                    f"```python\n{code}\n```",
                )
            )

        t3_blocks: List[ContextBlock] = []
        loaded_skills = skills if skills is not None else self.load_skills_for_role("remediation")
        for idx, skill_text in enumerate(loaded_skills, 1):
            t3_blocks.append(
                ContextBlock(
                    ContextTierEnum.TIER_3_ARCHITECTURE,
                    f"Remediation Debugging Skill #{idx}",
                    skill_text,
                )
            )

        return self.assemble_prompt(
            PersonaViewType.REMEDIATION_VIEW,
            t0_blocks,
            t1_blocks,
            t2_blocks,
            t3_blocks,
        )
