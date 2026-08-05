from app.providers.llm.inference_engine import inference_engine
from app.schemas.llm import LLMResponse


class LLMManager:

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        preferred_providers: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:

        return inference_engine.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_providers=preferred_providers,
            temperature=temperature,
            max_tokens=max_tokens,
        )


llm_manager = LLMManager()