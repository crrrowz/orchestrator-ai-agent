"""Tests for OmniRoute AI Gateway integration and routing."""

import os
from unittest.mock import patch, MagicMock
from orchestrator.core.config import AgentRoleConfig, OrchestratorConfig
from orchestrator.llm.factory import create_llm_for_role
from orchestrator.analysis.connectivity import ConnectivityChecker


def test_omniroute_config_defaults():
    with patch.dict(os.environ, {
        "OMNIROUTE_API_KEY": "sk-test-key",
        "OMNIROUTE_BASE_URL": "http://localhost:20128/v1",
        "PROVIDER": "omniroute",
    }, clear=False):
        config = OrchestratorConfig()
        assert config.omniroute_api_key == "sk-test-key"
        assert config.omniroute_base_url == "http://localhost:20128/v1"
        assert config.provider == "omniroute"


def test_create_llm_for_omniroute_role():
    config = OrchestratorConfig(
        omniroute_api_key="sk-test-key",
        omniroute_base_url="http://localhost:20128/v1",
    )
    role_config = AgentRoleConfig(
        role="developer",
        model="omniroute/auto/best-coding",
        temperature=0.2,
    )
    llm = create_llm_for_role(config, role_config)
    assert llm.model == "openai/auto/best-coding"
    assert llm.base_url == "http://localhost:20128/v1"
    assert llm.api_key.get_secret_value() == "sk-test-key"


def test_omniroute_connectivity_checker_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "auto/best-coding"},
            {"id": "auto/fast"},
        ]
    }
    with patch("httpx.Client.get", return_value=mock_resp):
        res = ConnectivityChecker.check_omniroute(
            base_url="http://localhost:20128/v1",
            api_key="sk-test-key",
            required_models=["omniroute/auto/best-coding", "omniroute/auto/unknown"],
        )
        assert res["connected"] is True
        assert res["models_status"]["omniroute/auto/best-coding"] is True
        assert res["models_status"]["omniroute/auto/unknown"] is False
