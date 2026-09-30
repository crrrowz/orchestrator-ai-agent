"""Unit tests for dynamic custom provider and model resolution."""

import os
from unittest.mock import MagicMock, patch
import pytest

from orchestrator.analysis.connectivity import ConnectivityChecker
from orchestrator.core.config import AgentRoleConfig, OrchestratorConfig
from orchestrator.llm.factory import create_llm_for_role, sanitize_base_url
from orchestrator.llm.pricing import get_pricing_rates


def test_sanitize_base_url():
    """Verify URL sanitization handles malformed ports and trailing slashes."""
    assert sanitize_base_url("http://127.0.0.1/:20128/v1") == "http://127.0.0.1:20128/v1"
    assert sanitize_base_url("http://127.0.0.1///:20128/v1/") == "http://127.0.0.1:20128/v1"
    assert sanitize_base_url("http://localhost:20128/v1/") == "http://localhost:20128/v1"
    assert sanitize_base_url("  http://localhost:8000/v1  ") == "http://localhost:8000/v1"
    assert sanitize_base_url(None) is None
    assert sanitize_base_url("") is None


def test_standard_provider_resolution_gemini():
    """Standard known provider passes directly with original prefix and credentials."""
    config = OrchestratorConfig(
        gemini_api_key="AQ-test-gemini-key",
        provider="gemini",
    )
    role_config = AgentRoleConfig(
        role="developer",
        model="gemini/gemini-2.0-flash",
    )
    llm = create_llm_for_role(config, role_config)
    assert llm.model == "gemini/gemini-2.0-flash"
    assert llm.api_key.get_secret_value() == "AQ-test-gemini-key"
    assert llm.base_url is None


def test_explicit_omniroute_prefix_routing():
    """Explicit omniroute prefix translates to openai/<model> with OmniRoute base URL and key."""
    config = OrchestratorConfig(
        omniroute_api_key="sk-omni-secret",
        omniroute_base_url="http://127.0.0.1/:20128/v1",
        provider="omniroute",
    )
    role_config = AgentRoleConfig(
        role="developer",
        model="omniroute/antigravity/gemini-3.7-flash-tiered",
    )
    llm = create_llm_for_role(config, role_config)
    assert llm.model == "openai/antigravity/gemini-3.7-flash-tiered"
    assert llm.base_url == "http://127.0.0.1:20128/v1"
    assert llm.api_key.get_secret_value() == "sk-omni-secret"


def test_custom_unknown_prefix_dynamic_routing_omniroute():
    """Unknown provider slug (like antigravity/...) routes dynamically via active OmniRoute gateway."""
    config = OrchestratorConfig(
        omniroute_api_key="sk-omni-secret",
        omniroute_base_url="http://127.0.0.1:20128/v1",
        provider="omniroute",
    )
    role_config = AgentRoleConfig(
        role="developer",
        model="antigravity/gemini-3.7-flash-tiered",
    )
    llm = create_llm_for_role(config, role_config)
    assert llm.model == "openai/antigravity/gemini-3.7-flash-tiered"
    assert llm.base_url == "http://127.0.0.1:20128/v1"
    assert llm.api_key.get_secret_value() == "sk-omni-secret"


def test_custom_unknown_prefix_dynamic_routing_openai_base():
    """Unknown provider slug routes via OPENAI_BASE_URL when active."""
    config = OrchestratorConfig(
        openai_api_key="sk-custom-openai-key",
        openai_base_url="http://localhost:8000/v1/",
        provider="openai",
    )
    role_config = AgentRoleConfig(
        role="tester",
        model="custom-org/my-fine-tuned-model",
    )
    llm = create_llm_for_role(config, role_config)
    assert llm.model == "openai/custom-org/my-fine-tuned-model"
    assert llm.base_url == "http://localhost:8000/v1"
    assert llm.api_key.get_secret_value() == "sk-custom-openai-key"


def test_pricing_for_gemini_37_flash():
    """Pricing calculation accurately identifies gemini-3.7 rates."""
    in_rate, out_rate = get_pricing_rates("antigravity/gemini-3.7-flash-tiered")
    assert in_rate == 0.10
    assert out_rate == 0.40


def test_connectivity_checker_sanitizes_omniroute_url():
    """ConnectivityChecker sanitizes malformed OmniRoute URLs when checking endpoints."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "antigravity/gemini-3.7-flash-tiered"},
            {"id": "auto/best-coding"},
        ]
    }
    with patch("httpx.Client.get", return_value=mock_resp) as mock_get:
        res = ConnectivityChecker.check_omniroute(
            base_url="http://127.0.0.1/:20128/v1/",
            api_key="sk-test-key",
            required_models=[
                "antigravity/gemini-3.7-flash-tiered",
                "omniroute/antigravity/gemini-3.7-flash-tiered",
                "unknown/model",
            ],
        )
        # Check that the GET call used sanitized URL without /:20128
        mock_get.assert_called_once_with(
            "http://127.0.0.1:20128/v1/models",
            headers={"Authorization": "Bearer sk-test-key"},
        )
        assert res["connected"] is True
        assert res["models_status"]["antigravity/gemini-3.7-flash-tiered"] is True
        assert res["models_status"]["omniroute/antigravity/gemini-3.7-flash-tiered"] is True
        assert res["models_status"]["unknown/model"] is False
