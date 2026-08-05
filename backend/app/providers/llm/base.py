from abc import ABC, abstractmethod

from app.schemas.llm import LLMResponse


class BaseLLMProvider(ABC):
    """
    Base interface for all LLM providers.
    Every provider must implement this interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check whether the provider is available.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """
        Return provider name.
        """
        pass