import ollama

from app.core.config import settings
from app.providers.llm.base import BaseLLMProvider
from app.providers.llm.base_provider import BaseProvider
from app.schemas.llm import LLMResponse


class OllamaProvider(BaseLLMProvider, BaseProvider):

    def __init__(self):
        self.client = ollama.Client(
            host=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_REQUEST_TIMEOUT_SECONDS,
        )

    def provider_name(self) -> str:
        return "Ollama"

    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:

        messages: list[dict] = []

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

            print(f"[Ollama] Model: {settings.OLLAMA_MODEL}")
            print(f"[Ollama] Prompt length: {len(prompt)}")
            print("[Ollama] Sending request...")

            response = self.client.chat(
                model=settings.OLLAMA_MODEL,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            latency = self.calculate_latency(start)

            return self.success_response(
                provider=self.provider_name(),
                model=settings.OLLAMA_MODEL,
                content=response["message"]["content"],
                latency_ms=latency,
                metadata={
                    "done": response.get("done"),
                    "done_reason": response.get("done_reason"),
                    "eval_count": response.get("eval_count"),
                    "eval_duration": response.get("eval_duration"),
                    "prompt_eval_count": response.get(
                        "prompt_eval_count"
                    ),
                    "prompt_eval_duration": response.get(
                        "prompt_eval_duration"
                    ),
                    "load_duration": response.get(
                        "load_duration"
                    ),
                    "total_duration": response.get(
                        "total_duration"
                    ),
                },
            )

        except Exception as e:

            return self.error_response(
                provider=self.provider_name(),
                model=settings.OLLAMA_MODEL,
                error=str(e),
            )