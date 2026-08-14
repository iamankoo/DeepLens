import time

from mistralai import Mistral

from app.core.config import settings
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.base_provider import BaseProvider
from app.schemas.llm import LLMResponse


class MistralProvider(BaseLLMProvider, BaseProvider):

    def __init__(self):
        self.client = Mistral(
            api_key=settings.MISTRAL_API_KEY,
            timeout_ms=settings.LLM_REQUEST_TIMEOUT_SECONDS * 1000,
        )

    def provider_name(self) -> str:
        return "Mistral"

    def is_available(self) -> bool:
        return bool(settings.MISTRAL_API_KEY)

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

            response = self.client.chat.complete(
                model=settings.MISTRAL_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            latency = self.calculate_latency(start)

            return self.success_response(
                provider=self.provider_name(),
                model=settings.MISTRAL_MODEL,
                content=response.choices[0].message.content,
                latency_ms=latency,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": (
                        response.usage.model_dump()
                        if response.usage
                        else {}
                    ),
                },
            )

        except Exception as e:

            return self.error_response(
                provider=self.provider_name(),
                model=settings.MISTRAL_MODEL,
                error=str(e),
            )