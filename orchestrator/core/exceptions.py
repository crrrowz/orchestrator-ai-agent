"""Central custom exceptions for orchestrator execution and error boundaries."""


class OrchestratorException(Exception):
    """Base exception for all orchestrator-related failures."""


class BudgetExhaustedError(OrchestratorException):
    """Raised when monetary or token budget ceiling has been reached."""


class CircuitBreakerTrippedError(OrchestratorException):
    """Raised when repeated identical failures trip the circuit breaker."""


class PipelineAbortedError(OrchestratorException):
    """Raised when pipeline execution is halted manually or via safety guard."""


class PreflightCheckError(OrchestratorException):
    """Raised when static preflight checks fail before agent execution."""


class HumanRejectedError(OrchestratorException):
    """Raised when a human operator rejects changes at an approval gate."""


class ProviderQuotaExceededError(OrchestratorException):
    """Raised when an upstream LLM provider rate limit or quota ceiling is hit."""

    def __init__(
        self,
        provider: str = "LLM Provider",
        message: str = "Provider quota or rate limit exceeded.",
        reset_info: str = "",
        remedy: str = "",
    ):
        super().__init__(message)
        self.provider = provider
        self.message = message
        self.reset_info = reset_info
        self.remedy = remedy
