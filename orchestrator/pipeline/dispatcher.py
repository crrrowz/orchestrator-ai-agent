"""Master Orchestrator Dispatcher (The Strangler Control Plane Seam).

Module: orchestrator.pipeline.dispatcher
Specification: docs/plans/P12_STRANGLER_FIG_MIGRATION_AND_SAFE_ROLLOUT_PLAN.md

Unifies CLI and API execution modes across the active Strangler Seam,
routing traffic dynamically to GuardedFSMEngine or transparently falling back
to legacy pipelines with comprehensive health verification.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from orchestrator.config import OrchestratorConfig, SkillManager
from orchestrator.control.human_channel import HumanChannel
from orchestrator.control.pipeline_controller import PipelineController
from orchestrator.pipeline.checkpoint import PipelineCheckpoint
from orchestrator.pipeline.fsm.engine import GuardedFSMEngine
from orchestrator.pipeline.fsm.profiles import LifecycleProfile, PipelineMode, get_profile
from orchestrator.pipeline.migration_guard import (
    CircuitBreakerStatus,
    ExecutionPlane,
    MigrationGuard,
)

logger = logging.getLogger("orchestrator.pipeline.dispatcher")


class OrchestratorDispatcher:
    """Master Dispatcher governing execution routing between GuardedFSMEngine and Legacy pipelines."""

    def __init__(
        self,
        migration_guard: Optional[MigrationGuard] = None,
    ) -> None:
        self.guard = migration_guard or MigrationGuard.get_instance()

    def dispatch(
        self,
        task: str,
        mode: str = "dev-test",
        config: Optional[OrchestratorConfig] = None,
        skill_manager: Optional[SkillManager] = None,
        workspace: Optional[Path] = None,
        checkpoint: Optional[PipelineCheckpoint] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[HumanChannel] = None,
        legacy_pipeline: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Dispatch task through GuardedFSMEngine (target) or Legacy fallback."""
        cfg = config or OrchestratorConfig()
        sm = skill_manager or SkillManager()
        ws = (workspace or cfg.workspace_path).resolve()
        clean_mode = str(mode).strip().lower().replace("_", "-")

        # Determine route via MigrationGuard
        route_to_modern = self.guard.should_route_to_modern(
            mode=clean_mode, task=task, workspace=ws
        )

        if route_to_modern:
            t0 = time.perf_counter()
            logger.info(
                "[STRANGLER SEAM] Routing mode '%s' to TARGET Hexagonal GuardedFSMEngine (Canary: %d%%)...",
                clean_mode,
                self.guard.config.canary_percentage,
            )
            profile: LifecycleProfile = get_profile(clean_mode)

            # Wire live visualizer and session store so progress and thoughts are visible
            log_store = getattr(legacy_pipeline, "store", None)
            visualizer = getattr(legacy_pipeline, "visualizer", None)
            if log_store is None:
                try:
                    from orchestrator.ui.session_store import SessionLogStore
                    log_store = SessionLogStore(workspace_path=ws)
                except Exception:
                    log_store = None
            if visualizer is None and log_store is not None:
                try:
                    from orchestrator.ui.visualizer import OrchestratorLiveVisualizer
                    visualizer = OrchestratorLiveVisualizer(
                        log_store=log_store,
                        verbosity=getattr(cfg, "verbosity", "normal"),
                    )
                except Exception:
                    visualizer = None

            try:
                engine = GuardedFSMEngine(
                    config=cfg,
                    skill_manager=sm,
                    profile=profile,
                    workspace_path=ws,
                    controller=controller,
                    human_channel=human_channel,
                    log_store=log_store,
                    visualizer=visualizer,
                )
                resume_flag = bool(kwargs.get("resume", False) or checkpoint is not None)
                raw_res = engine.run(task_description=task, resume=resume_flag)
                duration = time.perf_counter() - t0

                # Synthesize conforming result dictionary
                conforming_res = self._format_conforming_result(
                    raw_res=raw_res,
                    plane=ExecutionPlane.MODERN_GUARDED_FSM,
                    mode=clean_mode,
                )

                if conforming_res.get("success", False):
                    self.guard.record_success(
                        plane=ExecutionPlane.MODERN_GUARDED_FSM,
                        task_id=conforming_res.get("run_id", ""),
                        mode=clean_mode,
                        duration_seconds=duration,
                    )
                else:
                    self.guard.record_failure(
                        plane=ExecutionPlane.MODERN_GUARDED_FSM,
                        error=conforming_res.get("error_message")
                        or conforming_res.get("status")
                        or "FSM Run Failed",
                        task_id=conforming_res.get("run_id", ""),
                        mode=clean_mode,
                        duration_seconds=duration,
                    )
                return conforming_res

            except Exception as ex:
                duration = time.perf_counter() - t0
                logger.error(
                    "[STRANGLER SEAM] GuardedFSMEngine execution failure: %s",
                    ex,
                    exc_info=True,
                )

                fallback_enabled = self.guard.config.fallback_to_legacy_on_error
                self.guard.record_failure(
                    plane=ExecutionPlane.MODERN_GUARDED_FSM,
                    error=ex,
                    mode=clean_mode,
                    duration_seconds=duration,
                    fallback_triggered=False,
                )

                if fallback_enabled:
                    logger.warning(
                        "[STRANGLER SEAM] Auto-fallback engaged: executing task on LEGACY pipeline..."
                    )
                    return self.run_legacy(
                        task=task,
                        mode=clean_mode,
                        config=cfg,
                        skill_manager=sm,
                        workspace=ws,
                        checkpoint=checkpoint,
                        controller=controller,
                        human_channel=human_channel,
                        legacy_pipeline=legacy_pipeline,
                        fallback=True,
                        **kwargs,
                    )
                raise

        # Route to legacy pipeline fallback
        logger.info(
            "[STRANGLER SEAM] Routing mode '%s' to LEGACY fallback pipeline...", clean_mode
        )
        return self.run_legacy(
            task=task,
            mode=clean_mode,
            config=cfg,
            skill_manager=sm,
            workspace=ws,
            checkpoint=checkpoint,
            controller=controller,
            human_channel=human_channel,
            legacy_pipeline=legacy_pipeline,
            fallback=False,
            **kwargs,
        )

    def run_legacy(
        self,
        task: str,
        mode: str,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace: Path,
        checkpoint: Optional[PipelineCheckpoint] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[HumanChannel] = None,
        legacy_pipeline: Optional[Any] = None,
        fallback: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute task via legacy pipeline instance and record telemetry."""
        t0 = time.perf_counter()
        pipe = legacy_pipeline or self._create_legacy_pipeline(
            mode=mode,
            config=config,
            skill_manager=skill_manager,
            workspace=workspace,
            checkpoint=checkpoint,
            controller=controller,
            human_channel=human_channel,
        )

        try:
            # If the pipeline object has a dedicated legacy runner method, use it to avoid recursion
            if hasattr(pipe, "_run_legacy"):
                raw_res = pipe._run_legacy(task)
            else:
                raw_res = pipe.run(task)

            duration = time.perf_counter() - t0
            conforming_res = self._format_conforming_result(
                raw_res=raw_res,
                plane=ExecutionPlane.LEGACY_FALLBACK,
                mode=mode,
            )

            if conforming_res.get("success", False):
                self.guard.record_success(
                    plane=ExecutionPlane.LEGACY_FALLBACK,
                    task_id=conforming_res.get("run_id", ""),
                    mode=mode,
                    duration_seconds=duration,
                    fallback_triggered=fallback,
                )
            else:
                self.guard.record_failure(
                    plane=ExecutionPlane.LEGACY_FALLBACK,
                    error=conforming_res.get("error_message")
                    or conforming_res.get("status")
                    or "Legacy Run Failed",
                    task_id=conforming_res.get("run_id", ""),
                    mode=mode,
                    duration_seconds=duration,
                    fallback_triggered=fallback,
                )
            return conforming_res

        except Exception as ex:
            duration = time.perf_counter() - t0
            logger.error("[STRANGLER SEAM] Legacy pipeline failure: %s", ex, exc_info=True)
            self.guard.record_failure(
                plane=ExecutionPlane.LEGACY_FALLBACK,
                error=ex,
                mode=mode,
                duration_seconds=duration,
                fallback_triggered=fallback,
            )
            raise

    def _create_legacy_pipeline(
        self,
        mode: str,
        config: OrchestratorConfig,
        skill_manager: SkillManager,
        workspace: Path,
        checkpoint: Optional[PipelineCheckpoint] = None,
        controller: Optional[PipelineController] = None,
        human_channel: Optional[HumanChannel] = None,
    ) -> Any:
        """Instantiate corresponding legacy pipeline class for the given mode."""
        import importlib
        clean_mode = str(mode).strip().lower().replace("_", "-")

        if clean_mode == "audit":
            mod = importlib.import_module("orchestrator.pipeline.audit_pipeline")
            return mod.AuditPipeline(
                config=config,
                skill_manager=skill_manager,
                workspace_path=workspace,
                human_channel=human_channel,
                controller=controller,
            )
        elif clean_mode == "audit-fix":
            mod = importlib.import_module("orchestrator.pipeline.audit_fix_pipeline")
            return mod.AuditFixPipeline(
                config=config,
                skill_manager=skill_manager,
                workspace_path=workspace,
                human_channel=human_channel,
                controller=controller,
            )
        elif clean_mode == "docs":
            mod = importlib.import_module("orchestrator.pipeline.documentation_pipeline")
            return mod.DocumentationPipeline(
                config=config,
                skill_manager=skill_manager,
                workspace_path=workspace,
                human_channel=human_channel,
                controller=controller,
            )
        elif clean_mode == "full":
            mod = importlib.import_module("orchestrator.pipeline.full_pipeline")
            return mod.FullPipeline(
                config=config,
                skill_manager=skill_manager,
                workspace_path=workspace,
                checkpoint=checkpoint,
                controller=controller,
                human_channel=human_channel,
            )
        else:
            mod = importlib.import_module("orchestrator.pipeline.dev_test_loop")
            return mod.DevTestLoop(
                config=config,
                skill_manager=skill_manager,
                workspace_path=workspace,
                checkpoint=checkpoint,
                controller=controller,
                human_channel=human_channel,
            )

    @staticmethod
    def _format_conforming_result(
        raw_res: Dict[str, Any],
        plane: ExecutionPlane,
        mode: str,
    ) -> Dict[str, Any]:
        """Format uniform return dictionary conforming across both execution planes."""
        res = dict(raw_res) if isinstance(raw_res, dict) else {"raw": raw_res}
        res["plane"] = plane.value
        res["mode"] = mode

        # Normalize status and success fields
        status = res.get("status", "COMPLETED" if res.get("success") else "UNKNOWN")
        res["status"] = status

        if "success" not in res:
            res["success"] = status in (
                "SUCCESS",
                "COMPLETED",
                "CONVERGED_CLEAN",
                "AUDIT_COMPLETED",
                "DOCS_GENERATED",
            )

        # Standardize report_id and run_id compatibility
        run_id = res.get("run_id") or res.get("report_id") or ""
        res["run_id"] = run_id
        if "report_id" not in res:
            res["report_id"] = run_id

        # Standardize numeric metric keys
        res.setdefault("iterations", 1)
        res.setdefault("tokens_consumed", 0)
        res.setdefault("cost_usd", 0.0)
        res.setdefault("mutated_files", [])
        res.setdefault("error_message", None)

        return res


# Canonical alias matching P12 specification naming
StranglerPipelineDispatcher = OrchestratorDispatcher
