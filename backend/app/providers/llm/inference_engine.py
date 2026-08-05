from app.core.config import settings
from app.providers.llm.registry import provider_registry
from app.schemas.llm import LLMResponse


class InferenceEngine:

    def __init__(self):
        self.registry = provider_registry

    def generate(
        self,
        preferred_providers: list[str] | None = None,
        prompt: str = "",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        
        if preferred_providers is None:
            preferred_providers = [
                "groq",
                "gemini",
                "ollama",
            ]
            
        last_response: LLMResponse | None = None

        for provider_name in preferred_providers:

            provider = self.registry.get(provider_name)

            if provider is None:
                continue

            if not provider.is_available():
                continue

            response = provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if response.success:
                return response

            last_response = response

        if last_response:
            return last_response

        return LLMResponse(
            provider="none",
            model="unknown",
            content="",
            success=False,
            latency_ms=0.0,
            error="No available provider found.",
            metadata={},
        )


inference_engine = InferenceEngine()