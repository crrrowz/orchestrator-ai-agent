"""Unit tests for quiet visualizer, session log store, and interactive log explorer."""

from pathlib import Path
from orchestrator.ui.log_explorer import InteractiveLogExplorer
from orchestrator.ui.session_store import SessionLogStore


def test_session_log_store_add_and_save(tmp_path: Path):
    store = SessionLogStore(workspace_path=tmp_path)
    store.set_agent_context("Developer", "Writing Code")

    step1 = store.add_step(
        summary="workspace_file (write index.html)",
        action_type="WorkspaceFileAction",
        arguments={"path": "index.html", "operation": "write"},
        thought="Writing index.html for the user",
        observation="File written successfully",
        is_error=False,
    )

    assert step1.index == 1
    assert step1.role == "Developer"
    assert len(store.steps) == 1
    assert len(store.milestones) == 1

    # Save to file
    out_file = store.save_to_file(tmp_path)
    assert out_file.exists()
    assert "workspace_file (write index.html)" in out_file.read_text(encoding="utf-8")


def test_interactive_log_explorer_render(tmp_path: Path):
    store = SessionLogStore(workspace_path=tmp_path)
    store.set_agent_context("Architect", "Decomposition")
    store.add_step(
        summary="workspace_file (write PLAN.md)",
        action_type="WorkspaceFileAction",
        arguments={"path": "PLAN.md", "operation": "write"},
        thought="Designing blueprint",
        observation="PLAN.md created",
    )

    explorer = InteractiveLogExplorer(store)
    panel = explorer.render_view()
    assert panel is not None

    # Test expanding dropdown
    explorer.expanded_indices.add(0)
    panel_expanded = explorer.render_view()
    assert panel_expanded is not None
