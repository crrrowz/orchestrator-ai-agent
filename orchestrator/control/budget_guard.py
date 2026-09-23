"""Token and USD budget guard for runtime cost control."""


class BudgetGuard:
    """Monitors live accumulated spend and enforces hard cost caps."""

    def __init__(self, max_budget_usd: float = 0.50):
        self.max_budget_usd = max_budget_usd
        self.is_exhausted: bool = False
        self._current_cost_usd: float = 0.0

    def update_cost(self, cost_usd: float) -> bool:
        """Update current cost. Returns True if budget is exceeded."""
        try:
            self._current_cost_usd = float(cost_usd)
        except (TypeError, ValueError):
            self._current_cost_usd = 0.0

        if self.max_budget_usd > 0 and self._current_cost_usd >= self.max_budget_usd:
            self.is_exhausted = True
            return True
        return False

    @property
    def remaining_budget(self) -> float:
        """Calculate remaining dollar budget before ceiling."""
        if self.max_budget_usd <= 0:
            return float("inf")
        return max(0.0, self.max_budget_usd - self._current_cost_usd)
