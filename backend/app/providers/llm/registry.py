from app.core.logger import logger
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.groq_provider import GroqProvider
from app.providers.llm.mistral_provider import MistralProvider
from app.providers.llm.ollama_provider import OllamaProvider


class ProviderRegistry:

    def __init__(self):

        self.providers = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "mistral": MistralProvider(),
            "ollama": OllamaProvider(),
        }

        # Registered once per process (API server and worker each build
        # their own ProviderRegistry singleton) — logs whether each
        # provider's own is_available() check (API key present, or for
        # Ollama a live reachability probe) passes at startup, so a
        # misconfigured .env is visible immediately instead of only
        # surfacing as a mysterious failure during a research run.
        for name, provider in self.providers.items():
            try:
                available = provider.is_available()
            except Exception as e:
                available = False
                logger.warning(f"provider '{name}' is_available() raised at startup: {e}")
            logger.info(f"LLM provider registered: {name} (is_available={available})")

    def get(self, provider_name: str):

        return self.providers.get(provider_name)

    def all(self):

        return list(self.providers.values())


provider_registry = ProviderRegistry()