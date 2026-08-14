import time
import traceback

from app.core.logger import logger
from app.providers.llm.health import provider_health
from app.providers.llm.registry import provider_registry
from app.schemas.llm import LLMResponse

ALL_PROVIDERS_UNAVAILABLE_MESSAGE = "All configured LLM providers are currently unavailable."

DEFAULT_PROVIDER_ORDER = ["groq", "gemini", "mistral", "ollama"]


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
            preferred_providers = DEFAULT_PROVIDER_ORDER

        # Skip providers already known-bad this session (quota/rate-limit/
        # unavailable, per provider_health's cooldown) and try the rest in
        # order of recent success rate rather than the fixed default order —
        # requirements: skip exhausted providers instantly, never retry a
        # known-exhausted provider, auto-prioritize by recent success.
        candidates = provider_health.ordered_candidates(preferred_providers)

        print("\n========================================================")
        print("[InferenceEngine] Starting inference")
        print(f"[InferenceEngine] Prompt Length : {len(prompt)}")
        print(f"[InferenceEngine] Max Tokens   : {max_tokens}")
        print(f"[InferenceEngine] Configured   : {preferred_providers}")
        print(f"[InferenceEngine] Candidates   : {candidates} (cooled-down providers skipped)")
        print("========================================================")

        if not candidates:
            logger.error(
                "no LLM provider candidates available — all in cooldown",
                extra={"configured_providers": preferred_providers, "health": provider_health.snapshot()},
            )
            return LLMResponse(
                provider="none",
                model="unknown",
                content="",
                success=False,
                latency_ms=0.0,
                error=ALL_PROVIDERS_UNAVAILABLE_MESSAGE,
                metadata={"provider_health": provider_health.snapshot()},
            )

        last_response: LLMResponse | None = None

        for provider_name in candidates:

            print(f"\n[InferenceEngine] Trying provider: {provider_name}")

            provider = self.registry.get(provider_name)

            if provider is None:
                print(f"[InferenceEngine] Provider '{provider_name}' not registered")
                continue

            try:
                available = provider.is_available()
                print(f"[InferenceEngine] Available: {available}")
            except Exception:
                print("[InferenceEngine] is_available() crashed")
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

                elapsed_ms = (time.perf_counter() - start) * 1000

                print(
                    f"[InferenceEngine] {provider_name} returned "
                    f"(success={response.success}) "
                    f"in {elapsed_ms / 1000:.2f}s"
                )

                if response.success:
                    provider_health.record_success(provider_name, elapsed_ms)
                    return response

                provider_health.record_failure(provider_name, response.error or "unknown error")
                last_response = response

            except Exception as e:

                print(f"[InferenceEngine] {provider_name} crashed")
                print(traceback.format_exc())
                provider_health.record_failure(provider_name, str(e))

        print("\n[InferenceEngine] No provider succeeded.")

        if last_response:
            return last_response

        return LLMResponse(
            provider="none",
            model="unknown",
            content="",
            success=False,
            latency_ms=0.0,
            error=ALL_PROVIDERS_UNAVAILABLE_MESSAGE,
            metadata={"provider_health": provider_health.snapshot()},
        )


inference_engine = InferenceEngine()
