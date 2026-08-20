from abc import ABC, abstractmethod


class BaseSearchProvider(ABC):

    @abstractmethod
    def search(self, query: str, timeout: float | None = None):
        pass
