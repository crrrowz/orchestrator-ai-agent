"""Unit tests for Phase P8: Token Efficiency Deep Cuts."""

from pathlib import Path
from unittest.mock import patch, MagicMock


from orchestrator.analysis.graft_context import GraftContextProvider
from orchestrator.config import OrchestratorConfig
from orchestrator.control.cost_estimator import CostEstimator
from orchestrator.memory import ConversationStore
from orchestrator.vcs.git_ops import GitOps


def test_memory_stopword_filtering_and_min_score(tmp_path: Path):
    """ConversationStore should ignore common stopwords and reject irrelevant matches below min_score."""
    store = ConversationStore(memory_dir=tmp_path)

    # Save a past memory about redis caching
    store.save_run_memory(
        task="Create Redis caching middleware with TTL",
        summary="Built RedisCache with get, set, and expire methods.",
        files_touched=["src/cache/redis.py"],
        tests_passed=True,
    )

    # 1. Query with generic task words that are stopwords ("create implement task with code")
    # Should not match because all words are filtered out by COMMON_TASK_STOPWORDS
    results_generic = store.find_relevant_memories(
        "Create and implement task with code", min_score=3.0
    )
    assert len(results_generic) == 0

    # 2. Query with unrelated technical words ("PostgreSQL database migration")
    # No word overlap with Redis cache
    results_unrelated = store.find_relevant_memories(
        "PostgreSQL database migration", min_score=3.0
    )
    assert len(results_unrelated) == 0

    # 3. Query with relevant technical terms ("Redis cache invalidation")
    results_relevant = store.find_relevant_memories(
        "Redis cache invalidation", min_score=3.0
    )
    assert len(results_relevant) == 1
    assert "Redis" in results_relevant[0].task


def test_no_memory_config_flag():
    """OrchestratorConfig.enable_memory should toggle on/off correctly."""
    cfg_default = OrchestratorConfig()
    assert cfg_default.enable_memory is True

    cfg_disabled = OrchestratorConfig(enable_memory=False)
    assert cfg_disabled.enable_memory is False


def test_graft_freshness_caching(tmp_path: Path):
    """GraftContextProvider.build_index should skip execution if graft/ directory was modified < 300s ago."""
    graft_dir = tmp_path / "graft"
    graft_dir.mkdir(parents=True)

    with (
        patch.object(GraftContextProvider, "is_graft_available", return_value=True),
        patch("subprocess.run") as mock_subproc,
    ):
        # Fresh index (< 300s old): should NOT call subprocess.run
        fresh = GraftContextProvider.build_index(
            tmp_path, force=False, max_age_seconds=300.0
        )
        assert fresh is True
        mock_subproc.assert_not_called()

        # Forced rebuild: SHOULD call subprocess.run
        mock_subproc.return_value = MagicMock(returncode=0)
        rebuilt = GraftContextProvider.build_index(tmp_path, force=True)
        assert rebuilt is True
        mock_subproc.assert_called_once()


def test_git_ops_get_compact_diff_truncation(tmp_path: Path):
    """GitOps.get_compact_diff should provide stat summary and truncate oversized diffs."""
    git = GitOps(tmp_path)

    # Create mock diff outputs
    stat_output = " src/app.py | 120 +++++++++++++++++++++++++++++++++++++++++++++++\n 1 file changed, 120 insertions(+)"

    # 200 lines of diff
    diff_lines = [
        "diff --git a/src/app.py b/src/app.py",
        "--- a/src/app.py",
        "+++ b/src/app.py",
    ]
    for i in range(120):
        diff_lines.append(f"+    line_content_{i} = 'some payload data here'")
    diff_output = "\n".join(diff_lines)

    with patch.object(git, "_run_git") as mock_run:

        def side_effect(*args):
            mock_proc = MagicMock()
            if "--stat" in args:
                mock_proc.stdout = stat_output
            else:
                mock_proc.stdout = diff_output
            return mock_proc

        mock_run.side_effect = side_effect

        # Compact diff with max_lines_per_file=20
        compact = git.get_compact_diff(max_lines_per_file=20, max_chars=1000)

        assert "Diff Summary:" in compact
        assert "1 file changed" in compact
        assert (
            "[... diff truncated for this file ...]" in compact
            or "[... Diff truncated:" in compact
        )
        assert len(compact) <= 1200


def test_cost_estimator_calculation():
    """CostEstimator should calculate tokens and pricing for dev-test and full modes."""
    cfg = OrchestratorConfig()
    cfg.developer.model = "openrouter/qwen/qwen3.8-27b:free"
    cfg.tester.model = "openrouter/qwen/qwen3.8-27b:free"
    cfg.architect.model = "openrouter/qwen/qwen3.8-27b:free"
    cfg.reviewer.model = "openrouter/qwen/qwen3.8-27b:free"

    # dev-test mode
    res_dev = CostEstimator.estimate(
        "Implement JWT authentication with refresh token revocation",
        mode="dev-test",
        config=cfg,
    )
    assert res_dev.mode == "dev-test"
    assert len(res_dev.roles) == 2  # developer, tester
    assert res_dev.total_tokens > 0
    # Default developer model is free tier openrouter/qwen/qwen3.8-27b:free, so cost is $0.00
    assert res_dev.total_cost_usd == 0.0

    # full mode
    res_full = CostEstimator.estimate(
        "Implement JWT authentication with refresh token revocation",
        mode="full",
        config=cfg,
    )
    assert res_full.mode == "full"
    assert len(res_full.roles) == 4  # architect, developer, tester, reviewer
    assert res_full.total_tokens > res_dev.total_tokens


def test_cost_estimator_paid_model_pricing():
    """CostEstimator should calculate non-zero pricing for commercial models."""
    cfg = OrchestratorConfig()
    cfg.developer.model = "anthropic/claude-sonnet-4-5-20250929"
    cfg.reviewer.model = "openai/gpt-4o"

    res = CostEstimator.estimate("Build microservice", mode="full", config=cfg)
    assert res.total_cost_usd > 0.0
