import time
import traceback

from app.core.logger import logger
from app.providers.llm.health import format_provider_report, provider_health
from app.providers.llm.registry import provider_registry
from app.schemas.llm import LLMResponse

ALL_PROVIDERS_UNAVAILABLE_MESSAGE = "All configured LLM providers are currently unavailable."

DEFAULT_PROVIDER_ORDER = ["groq", "gemini", "mistral", "ollama"]


def _unavailable_response(preferred_providers: list[str]) -> LLMResponse:
    described = provider_health.describe(preferred_providers)
    logger.error(
        "no LLM provider succeeded — returning all-unavailable\n" + format_provider_report(described)
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

        # Log every configured provider's real-time status *before* deciding
        # anything, not just the ones that end up as candidates — this is
        # the exact picture needed to answer "why did provider X get
        # skipped" without guessing.
        described = provider_health.describe(preferred_providers)
        logger.info("provider status before inference\n" + format_provider_report(described))

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
            return _unavailable_response(preferred_providers)

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

            start = time.perf_counter()
            try:

                print(f"[InferenceEngine] Calling {provider_name}.generate()")

                # This is a real generation call, not a cheap availability
                # probe — is_available() above only checks the provider is
                # configured/reachable; success/failure of the actual model
                # response is what health tracking and failover are based on.
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

                elapsed_ms = (time.perf_counter() - start) * 1000
                print(f"[InferenceEngine] {provider_name} crashed")
                print(traceback.format_exc())
                provider_health.record_failure(provider_name, str(e))
                # Bug fixed here: this branch used to record the failure but
                # never set last_response, so a provider that raised (rather
                # than returning a clean success=False LLMResponse) had its
                # specific error silently discarded — every remaining
                # candidate failing this way produced the generic
                # all-unavailable message even though a real, specific error
                # was available and already logged above.
                last_response = LLMResponse(
                    provider=provider_name,
                    model="unknown",
                    content="",
                    success=False,
                    latency_ms=elapsed_ms,
                    error=str(e),
                    metadata={},
                )

        print("\n[InferenceEngine] No provider succeeded.")

        if last_response:
            logger.error(
                "no LLM provider succeeded — returning last provider's specific error\n"
                + format_provider_report(provider_health.describe(preferred_providers)),
                extra={"final_provider": last_response.provider, "final_error": last_response.error},
            )
            return last_response

        return _unavailable_response(preferred_providers)


inference_engine = InferenceEngine()
