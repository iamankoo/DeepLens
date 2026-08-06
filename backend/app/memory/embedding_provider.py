from abc import ABC, abstractmethod


class BaseEmbeddingProvider(ABC):

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for a piece of text.
        """
        pass

    @abstractmethod
    def provider_name(self) -> str:
        pass