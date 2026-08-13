import time
import traceback

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

        print("\n========================================================")
        print("[InferenceEngine] Starting inference")
        print(f"[InferenceEngine] Prompt Length : {len(prompt)}")
        print(f"[InferenceEngine] Max Tokens   : {max_tokens}")
        print(f"[InferenceEngine] Providers    : {preferred_providers}")
        print("========================================================")

        last_response: LLMResponse | None = None

        for provider_name in preferred_providers:

            print(f"\n[InferenceEngine] Trying provider: {provider_name}")

            provider = self.registry.get(provider_name)

            if provider is None:
                print(f"[InferenceEngine] Provider '{provider_name}' not registered")
                continue

            try:
                available = provider.is_available()
                print(f"[InferenceEngine] Available: {available}")
            except Exception:
                print(f"[InferenceEngine] is_available() crashed")
                print(traceback.format_exc())
                continue

            if not available:
                continue

            try:

                print(f"[InferenceEngine] Calling {provider_name}.generate()")

                start = time.perf_counter()

                response = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                elapsed = time.perf_counter() - start

                print(
                    f"[InferenceEngine] {provider_name} returned "
                    f"(success={response.success}) "
                    f"in {elapsed:.2f}s"
                )

                if response.success:
                    return response

                last_response = response

            except Exception:

                print(f"[InferenceEngine] {provider_name} crashed")
                print(traceback.format_exc())

        print("\n[InferenceEngine] No provider succeeded.")

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