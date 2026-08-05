from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.ollama_provider import OllamaProvider
from app.providers.llm.groq_provider import GroqProvider


class ProviderRegistry:

    def __init__(self):

        self.providers = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "mistral": MistralProvider(),
            "ollama": OllamaProvider(),
        }

    def get(self, provider_name: str):

        return self.providers.get(provider_name)

    def all(self):

        return list(self.providers.values())


provider_registry = ProviderRegistry()