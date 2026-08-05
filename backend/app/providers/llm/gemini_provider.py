from google import genai

from app.core.config import settings
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.base_provider import BaseProvider
from app.schemas.llm import LLMResponse


class GeminiProvider(BaseLLMProvider, BaseProvider):

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def provider_name(self) -> str:
        return "Gemini"

    def is_available(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:

        final_prompt = prompt

        if system_prompt:
            final_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            start = self.start_timer()

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=final_prompt,
            )

            latency = self.calculate_latency(start)

            return self.success_response(
                provider=self.provider_name(),
                model=settings.GEMINI_MODEL,
                content=response.text,
                latency_ms=latency,
                metadata={
                    "finish_reason": "STOP",
                },
            )

        except Exception as e:

            return self.error_response(
                provider=self.provider_name(),
                model=settings.GEMINI_MODEL,
                error=str(e),
            )