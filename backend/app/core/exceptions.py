class DeepLensError(Exception):
    """Base class for all application-raised (as opposed to unexpected) errors."""


class LLMProviderError(DeepLensError):
    """An LLM provider call failed or returned a non-success response."""


class OutputParsingError(DeepLensError):
    """An LLM response could not be parsed into the expected structured output."""
