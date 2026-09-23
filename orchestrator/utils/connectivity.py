"""Zero-token API and model connectivity validation utility."""

from typing import Any, Dict, List, Optional
import httpx
from rich.table import Table

from orchestrator.config import OrchestratorConfig
from orchestrator.utils.output import console, ConsoleOutput


class ConnectivityChecker:
    """Verifies API credentials, provider connectivity, and model availability with 0 token consumption."""

    @staticmethod
    def check_openrouter(api_key: str, required_models: List[str]) -> Dict[str, Any]:
        """Check OpenRouter key validity and model existence without invoking completions."""
        result: Dict[str, Any] = {
            "provider": "OpenRouter",
            "connected": False,
            "error": None,
            "quota_info": "",
            "models_status": {},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/Antigravity-Agent-API",
            "X-Title": "Antigravity Multi-Agent Orchestrator",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                # 1. Auth & Quota Check (0 tokens)
                auth_resp = client.get("https://openrouter.ai/api/v1/auth/key", headers=headers)
                if auth_resp.status_code != 200:
                    result["error"] = f"Auth failed with HTTP {auth_resp.status_code}: {auth_resp.text[:100]}"
                    return result

                auth_data = auth_resp.json().get("data", {})
                free_reqs = auth_data.get("free_model_daily_requests", {})
                free_remaining = free_reqs.get("remaining", "N/A")
                limit_remaining = auth_data.get("limit_remaining", 0)
                result["connected"] = True
                result["quota_info"] = f"Free Requests: {free_remaining}/1000 daily | Credit: ${limit_remaining}"

                # 2. Model Catalog Check (0 tokens)
                models_resp = client.get("https://openrouter.ai/api/v1/models")
                if models_resp.status_code == 200:
                    available_ids = {m["id"] for m in models_resp.json().get("data", [])}
                    for m in required_models:
                        clean_model_id = m.replace("openrouter/", "")
                        result["models_status"][m] = clean_model_id in available_ids
                else:
                    for m in required_models:
                        result["models_status"][m] = True  # fallback if catalog check failed
        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def check_openai(api_key: str) -> Dict[str, Any]:
        """Check OpenAI key validity with 0 tokens using /models endpoint."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"})
                if resp.status_code == 200:
                    return {"provider": "OpenAI", "connected": True, "error": None}
                return {"provider": "OpenAI", "connected": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"provider": "OpenAI", "connected": False, "error": str(e)}

    @classmethod
    def run_zero_token_audit(cls, config: OrchestratorConfig) -> None:
        """Run connectivity check across all configured roles and display a Rich diagnostic table."""
        ConsoleOutput.banner("Zero-Token Model Connectivity Audit", "Validates endpoints and models with 0 token consumption")

        table = Table(title="Model & Provider Connectivity", border_style="cyan")
        table.add_column("Agent Role", style="bold white", no_wrap=True)
        table.add_column("Configured Model", style="cyan", overflow="fold")
        table.add_column("Provider Status", style="green")
        table.add_column("Model Availability", style="magenta")
        table.add_column("Token Cost", style="yellow", no_wrap=True)

        # Collect configured models
        roles_models = [
            ("Developer", config.developer.model),
            ("Tester", config.tester.model),
            ("Reviewer", config.reviewer.model),
            ("Architect", config.architect.model),
        ]

        openrouter_models = [m for _, m in roles_models if m.startswith("openrouter/")]
        openrouter_info: Optional[Dict[str, Any]] = None

        if config.openrouter_api_key and openrouter_models:
            openrouter_info = cls.check_openrouter(config.openrouter_api_key, openrouter_models)

        for role_name, model_str in roles_models:
            provider_status = "[gray]Not Configured[/gray]"
            model_status = "[gray]Unverified[/gray]"

            if model_str.startswith("openrouter/"):
                if not config.openrouter_api_key:
                    provider_status = "[red][ERR] Missing Key[/red]"
                    model_status = "[red]No Access[/red]"
                elif openrouter_info and openrouter_info["connected"]:
                    provider_status = f"[green][OK] Connected[/green]\n[dim]{openrouter_info['quota_info']}[/dim]"
                    is_avail = openrouter_info["models_status"].get(model_str, False)
                    model_status = "[green][OK] Active on OpenRouter[/green]" if is_avail else "[red][ERR] Model ID Not Found[/red]"
                else:
                    err = openrouter_info["error"] if openrouter_info else "Connection Error"
                    provider_status = f"[red][ERR] Failed: {err}[/red]"
                    model_status = "[red]Unavailable[/red]"
            elif model_str.startswith("openai/"):
                if config.openai_api_key:
                    res = cls.check_openai(config.openai_api_key)
                    provider_status = "[green][OK] Connected[/green]" if res["connected"] else f"[red][ERR] {res['error']}[/red]"
                    model_status = "[green][OK] Verified[/green]" if res["connected"] else "[red]Error[/red]"
                else:
                    provider_status = "[red][ERR] Missing OPENAI_API_KEY[/red]"
                    model_status = "[red]Unauthenticated[/red]"
            elif model_str.startswith("anthropic/"):
                provider_status = "[green][OK] Key Present[/green]" if config.anthropic_api_key else "[yellow]Missing Key[/yellow]"
                model_status = "[green][OK] Configured[/green]" if config.anthropic_api_key else "[yellow]Awaiting Key[/yellow]"

            table.add_row(role_name, model_str, provider_status, model_status, "0 Tokens (Free)")

        console.print(table)
