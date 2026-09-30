"""Test for GUI CLI integration."""

import pytest
from orchestrator.cli.app import parse_args


def test_cli_gui_argument(monkeypatch):
    monkeypatch.setattr("sys.argv", ["main.py", "gui"])
    args = parse_args()
    assert args.task == "gui"

    monkeypatch.setattr("sys.argv", ["main.py", "--gui", "--port", "9000"])
    args = parse_args()
    assert args.gui is True
    assert args.port == 9000
