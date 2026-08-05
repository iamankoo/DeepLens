from groq import Groq

from app.core.config import settings
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.base_provider import BaseProvider
from app.schemas.llm import LLMResponse


class GroqProvider(BaseLLMProvider, BaseProvider):

    def __init__(self):
        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    def provider_name(self) -> str:
        return "Groq"

    def is_available(self) -> bool:
        return bool(settings.GROQ_API_KEY)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        try:

            start = self.start_timer()

            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            latency = self.calculate_latency(start)

            return self.success_response(
                provider=self.provider_name(),
                model=settings.GROQ_MODEL,
                content=response.choices[0].message.content,
                latency_ms=latency,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.model_dump(),
                },
            )

        except Exception as e:

            return self.error_response(
                provider=self.provider_name(),
                model=settings.GROQ_MODEL,
                error=str(e),
            )