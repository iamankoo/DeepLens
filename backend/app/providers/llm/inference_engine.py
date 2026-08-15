import time
import traceback

from app.core.config import settings
from app.core.logger import logger
from app.providers.llm.health import format_provider_report, provider_health
from app.providers.llm.registry import provider_registry
from app.schemas.llm import LLMResponse

ALL_PROVIDERS_UNAVAILABLE_MESSAGE = "All configured LLM providers are currently unavailable."

# Mandatory fallback priority (V1 requirement) — do not reorder. A provider
# is only skipped if it's in cooldown (see provider_health) or its call
# fails; the next one is always tried in this exact sequence. Ollama is
# included only when settings.ENABLE_OLLAMA is True (the local-dev default);
# production sets it False since there's no reachable local Ollama server,
# giving Groq -> Mistral -> Gemini instead of attempting an unreachable host.
DEFAULT_PROVIDER_ORDER = [
    p for p in ["groq", "mistral", "ollama", "gemini"] if p != "ollama" or settings.ENABLE_OLLAMA
]


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
        # the mandatory Groq → Mistral → Ollama → Gemini order — never
        # retry a known-exhausted provider, never reorder by success rate.
        candidates = provider_health.ordered_candidates(preferred_providers)

        logger.debug(
            "starting inference",
            extra={
                "prompt_length": len(prompt),
                "max_tokens": max_tokens,
                "configured_providers": preferred_providers,
                "candidates": candidates,
            },
        )

        if not candidates:
            return _unavailable_response(preferred_providers)

        last_response: LLMResponse | None = None

        for provider_name in candidates:

            provider = self.registry.get(provider_name)

            if provider is None:
                logger.warning("provider not registered", extra={"provider": provider_name})
                continue

            try:
                available = provider.is_available()
            except Exception:
                logger.error(
                    "provider.is_available() crashed",
                    extra={"provider": provider_name, "traceback": traceback.format_exc()},
                )
                continue

            if not available:
                continue

            start = time.perf_counter()
            try:

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

                logger.debug(
                    "provider call returned",
                    extra={"provider": provider_name, "success": response.success, "elapsed_ms": round(elapsed_ms, 1)},
                )

                if response.success:
                    provider_health.record_success(provider_name, elapsed_ms)
                    return response

                provider_health.record_failure(provider_name, response.error or "unknown error")
                last_response = response

            except Exception as e:

                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    "provider call crashed",
                    extra={"provider": provider_name, "elapsed_ms": round(elapsed_ms, 1), "traceback": traceback.format_exc()},
                )
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

        if last_response:
            logger.error(
                "no LLM provider succeeded — returning last provider's specific error\n"
                + format_provider_report(provider_health.describe(preferred_providers)),
                extra={"final_provider": last_response.provider, "final_error": last_response.error},
            )
            return last_response

        return _unavailable_response(preferred_providers)


inference_engine = InferenceEngine()
