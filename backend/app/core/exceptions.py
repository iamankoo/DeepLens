class DeepLensError(Exception):
    """Base class for all application-raised (as opposed to unexpected) errors."""


class LLMProviderError(DeepLensError):
    """An LLM provider call failed or returned a non-success response."""


class OutputParsingError(DeepLensError):
    """An LLM response could not be parsed into the expected structured output."""


class ResearchTimeoutError(DeepLensError):
    """A research run exceeded its wall-clock time budget (see
    Settings.RESEARCH_TIME_BUDGET_SECONDS) and was stopped cooperatively
    between workflow nodes by WorkflowManager, rather than by the harder
    RQ-level job_timeout (which would raise rq.timeouts.JobTimeoutException
    instead if this check didn't get a chance to run first)."""
