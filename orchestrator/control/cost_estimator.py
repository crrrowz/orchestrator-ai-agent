"""Pre-Execution Token and Cost Estimation Engine."""

from dataclasses import dataclass, field
from pathlib import Path
from rich.table import Table

from orchestrator.config import OrchestratorConfig
from orchestrator.utils.output import console


@dataclass
class RoleEstimate:
    role: str
    model: str
    calls_expected: int
    est_input_tokens: int
    est_output_tokens: int
    input_rate_per_m: float
    output_rate_per_m: float

    @property
    def est_cost_usd(self) -> float:
        input_cost = (self.est_input_tokens / 1_000_000.0) * self.input_rate_per_m
        output_cost = (self.est_output_tokens / 1_000_000.0) * self.output_rate_per_m
        return input_cost + output_cost

    @property
    def total_tokens(self) -> int:
        return self.est_input_tokens + self.est_output_tokens


@dataclass
class CostEstimateResult:
    task: str
    mode: str
    roles: list[RoleEstimate] = field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0


class CostEstimator:
    """Pre-computes expected token consumption and monetary cost without making LLM calls."""

    @staticmethod
    def get_pricing_rates(model: str) -> tuple[float, float]:
        """Return (input_rate_per_1M, output_rate_per_1M) in USD."""
        m = (model or "").lower()
        if ":free" in m or "openrouter/free" in m:
            return 0.0, 0.0
        if (
            "claude-sonnet-4-5" in m
            or "claude-3-5-sonnet" in m
            or "claude-3.5-sonnet" in m
        ):
            return 3.0, 15.0
        if "gpt-4o-mini" in m:
            return 0.15, 0.60
        if "gpt-4o" in m:
            return 2.50, 10.00
        if "gemini-2.0-flash" in m or "gemini-1.5-flash" in m:
            return 0.10, 0.40
        if "gemini-1.5-pro" in m:
            return 1.25, 5.00
        # Generic fallback
        return 1.00, 3.00

    @classmethod
    def estimate(
        cls,
        task: str,
        mode: str,
        config: OrchestratorConfig,
        assumed_iterations: int = 2,
    ) -> CostEstimateResult:
        """Estimate token burn and monetary cost based on task length, mode, and configured models."""
        task_text = task or ""
        clean_path = task_text.strip().strip("'\"")
        try:
            p = Path(clean_path)
            if p.exists() and p.is_file():
                task_text = p.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            pass

        task_words = len(task_text.split())
        task_tokens = int(task_words * 1.3)
        context_overhead = 1500  # system prompt + skill rules + graft summary

        if mode == "audit":
            role_configs = [
                ("auditor", config.reviewer.model, 1, 1500),
            ]
        elif mode == "full":
            role_configs = [
                ("architect", config.architect.model, 1, 1200),
                ("developer", config.developer.model, assumed_iterations, 2000),
                ("tester", config.tester.model, assumed_iterations, 800),
                ("reviewer", config.reviewer.model, 1, 600),
            ]
        else:
            role_configs = [
                ("developer", config.developer.model, assumed_iterations, 2000),
                ("tester", config.tester.model, assumed_iterations, 800),
            ]

        estimates: list[RoleEstimate] = []
        for role_name, model_name, calls, est_out_per_call in role_configs:
            in_rate, out_rate = cls.get_pricing_rates(model_name)
            # Input tokens scale with context overhead + task + previous history
            est_in = calls * (context_overhead + task_tokens + 500)
            est_out = calls * est_out_per_call
            estimates.append(
                RoleEstimate(
                    role=role_name,
                    model=model_name,
                    calls_expected=calls,
                    est_input_tokens=est_in,
                    est_output_tokens=est_out,
                    input_rate_per_m=in_rate,
                    output_rate_per_m=out_rate,
                )
            )

        total_toks = sum(e.total_tokens for e in estimates)
        total_cost = sum(e.est_cost_usd for e in estimates)

        return CostEstimateResult(
            task=task,
            mode=mode,
            roles=estimates,
            total_tokens=total_toks,
            total_cost_usd=total_cost,
        )

    @classmethod
    def render(cls, result: CostEstimateResult, config: OrchestratorConfig) -> None:
        """Render a formatted Rich table displaying the pre-execution token and cost projection."""
        table = Table(
            title=f"Pre-Execution Cost & Token Estimate ({result.mode.upper()} Mode)",
            header_style="bold cyan",
            border_style="dim",
        )
        table.add_column("Agent Role", style="bold magenta")
        table.add_column("Configured Model", style="green")
        table.add_column("Calls", justify="right")
        table.add_column("Est. Input Tokens", justify="right")
        table.add_column("Est. Output Tokens", justify="right")
        table.add_column("Est. Cost (USD)", justify="right")

        for r in result.roles:
            cost_str = (
                "$0.0000 (Free Tier)"
                if r.est_cost_usd == 0.0
                else f"${r.est_cost_usd:.4f}"
            )
            table.add_row(
                r.role.capitalize(),
                r.model,
                str(r.calls_expected),
                f"{r.est_input_tokens:,}",
                f"{r.est_output_tokens:,}",
                cost_str,
            )

        console.print(table)
        console.print(f"[bold]Total Projected Tokens:[/bold] {result.total_tokens:,}")
        console.print(
            f"[bold]Total Estimated Cost:[/bold] ${result.total_cost_usd:.4f} USD"
        )
        console.print(f"[dim]Budget Cap: ${config.max_budget_usd:.2f} USD[/dim]\n")
