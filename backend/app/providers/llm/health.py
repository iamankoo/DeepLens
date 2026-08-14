"""LLM provider health tracking, shared across the API and worker processes.

The API server and RQ worker are separate Python processes — the worker is
the one actually calling LLM providers, but the API process is what serves
GET /health/providers for monitoring. An in-memory singleton wouldn't be
visible across that process boundary, so this is backed by Redis (already a
hard dependency of this project via RQ) rather than a plain dict: one JSON
blob per provider, read-modify-write on every update. There's no locking
around that read-modify-write — under the low write frequency of LLM calls
from a single worker this is an acceptable tradeoff for a health/monitoring
feature, not something correctness-critical like a balance or a counter
that must never drift.
"""

import enum
import json
import re
import time
from dataclasses import dataclass

from app.core.config import settings
from app.core.logger import logger
from app.queue.connection import redis_conn

# ---- Error classification --------------------------------------------------


class ProviderStatus(str, enum.Enum):
    HEALTHY = "healthy"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    UNAVAILABLE = "unavailable"


# Substring/regex signals observed in real provider error text (Groq/OpenAI-
# style "Error code: 429 ... rate_limit_exceeded ... tokens per day", Gemini's
# "429 RESOURCE_EXHAUSTED ... generate_content_free_tier_requests"). Checked
# in order — quota (daily/hard cap) before generic rate limit, since a quota
# message often also contains the word "limit".
_QUOTA_SIGNALS = ("quota", "resource_exhausted", "tokens per day", "requests per day", "per_day")
_RATE_LIMIT_SIGNALS = ("rate_limit", "rate limit", "429", "too many requests")
_UNAVAILABLE_SIGNALS = ("timed out", "timeout", "connection", "unavailable", "503", "502", "econnrefused")

_RETRY_DELAY_PATTERNS = [
    re.compile(r"retrydelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", re.IGNORECASE),
    re.compile(r"retry in (\d+(?:\.\d+)?)\s*s", re.IGNORECASE),
    re.compile(r"try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s", re.IGNORECASE),
]


def classify_error(error: str) -> ProviderStatus:
    text = (error or "").lower()

    if any(signal in text for signal in _QUOTA_SIGNALS):
        return ProviderStatus.QUOTA_EXHAUSTED
    if any(signal in text for signal in _RATE_LIMIT_SIGNALS):
        return ProviderStatus.RATE_LIMITED
    if any(signal in text for signal in _UNAVAILABLE_SIGNALS):
        return ProviderStatus.UNAVAILABLE
    return ProviderStatus.UNAVAILABLE


def extract_retry_delay_seconds(error: str) -> float | None:
    """Respects a provider's own stated retry delay when it gives one
    (e.g. Gemini's `retryDelay: '25s'`, Groq's "try again in 12m4.896s")
    instead of guessing — falls back to the category default otherwise."""

    for pattern in _RETRY_DELAY_PATTERNS:
        match = pattern.search(error or "")
        if not match:
            continue
        groups = [g for g in match.groups() if g is not None]
        if len(groups) == 2:
            minutes, seconds = groups
            return float(minutes) * 60 + float(seconds)
        if len(groups) == 1:
            return float(groups[0])
    return None


# ---- Health state ------------------------------------------------------


@dataclass
class ProviderHealth:
    status: ProviderStatus = ProviderStatus.HEALTHY
    unavailable_until: float | None = None  # time.time() timestamp, None = available now
    last_error: str | None = None
    total_calls: int = 0
    total_successes: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float | None = None

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0  # untested providers get a fair first shot, not deprioritized
        return self.total_successes / self.total_calls

    @property
    def average_latency_ms(self) -> float:
        if self.total_successes == 0:
            return 0.0
        return self.total_latency_ms / self.total_successes

    def is_available(self) -> bool:
        return self.unavailable_until is None or time.time() >= self.unavailable_until

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "unavailable_until": self.unavailable_until,
            "last_error": self.last_error,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_latency_ms": self.total_latency_ms,
            "last_latency_ms": self.last_latency_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderHealth":
        return cls(
            status=ProviderStatus(data.get("status", ProviderStatus.HEALTHY.value)),
            unavailable_until=data.get("unavailable_until"),
            last_error=data.get("last_error"),
            total_calls=data.get("total_calls", 0),
            total_successes=data.get("total_successes", 0),
            total_latency_ms=data.get("total_latency_ms", 0.0),
            last_latency_ms=data.get("last_latency_ms"),
        )


class ProviderHealthTracker:

    REDIS_KEY = "deeplens:llm_provider_health"

    def __init__(
        self,
        *,
        quota_cooldown_seconds: float = 3600,
        rate_limit_cooldown_seconds: float = 60,
        unavailable_cooldown_seconds: float = 300,
    ):
        self._cooldowns = {
            ProviderStatus.QUOTA_EXHAUSTED: quota_cooldown_seconds,
            ProviderStatus.RATE_LIMITED: rate_limit_cooldown_seconds,
            ProviderStatus.UNAVAILABLE: unavailable_cooldown_seconds,
        }

    def _read_all(self) -> dict[str, ProviderHealth]:
        raw = redis_conn.get(self.REDIS_KEY)
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return {name: ProviderHealth.from_dict(h) for name, h in data.items()}
        except (ValueError, TypeError):
            logger.warning("provider health blob in redis was unreadable — resetting")
            return {}

    def _write_all(self, health_by_provider: dict[str, ProviderHealth]) -> None:
        payload = {name: health.to_dict() for name, health in health_by_provider.items()}
        redis_conn.set(self.REDIS_KEY, json.dumps(payload))

    def is_available(self, provider_name: str) -> bool:
        all_health = self._read_all()
        health = all_health.get(provider_name)
        return health is None or health.is_available()

    def record_success(self, provider_name: str, latency_ms: float) -> None:
        all_health = self._read_all()
        health = all_health.get(provider_name, ProviderHealth())
        health.status = ProviderStatus.HEALTHY
        health.unavailable_until = None
        health.last_error = None
        health.total_calls += 1
        health.total_successes += 1
        health.total_latency_ms += latency_ms
        health.last_latency_ms = latency_ms
        all_health[provider_name] = health
        self._write_all(all_health)

    def record_failure(self, provider_name: str, error: str) -> None:
        all_health = self._read_all()
        health = all_health.get(provider_name, ProviderHealth())
        status = classify_error(error)
        default_cooldown = self._cooldowns.get(status, 300)

        # A provider's own stated retry delay is authoritative when given
        # (it knows its actual quota/rate-limit window). Otherwise, scale
        # the category default by how reliable this provider has actually
        # been: a single timeout on a provider with a strong track record
        # (e.g. 88% success over 30+ calls) is far more likely a transient
        # blip than a real outage, and a full 300s "unavailable" cooldown
        # for it just wastes a good provider's availability for no reason.
        # Reproduced live: Mistral sat at 88% success over 33 calls, still
        # correctly excluded for a flat 5 minutes on one timeout.
        stated_delay = extract_retry_delay_seconds(error)
        if stated_delay is not None:
            cooldown = stated_delay
        elif health.total_calls >= 3 and health.success_rate >= 0.7:
            cooldown = max(15.0, default_cooldown * (1 - health.success_rate))
        else:
            cooldown = default_cooldown

        health.status = status
        health.unavailable_until = time.time() + cooldown
        health.last_error = error
        health.total_calls += 1
        all_health[provider_name] = health
        self._write_all(all_health)

        logger.warning(
            "provider marked unavailable",
            extra={
                "provider": provider_name,
                "status": status.value,
                "cooldown_s": round(cooldown, 1),
                "error": error[:200],
            },
        )

    def reset(self, provider_name: str | None = None) -> None:
        """Manually clears tracked health — one provider, or all of them if
        omitted. Not called automatically on backend/worker restart: health
        state is intentionally Redis-backed specifically so a real quota
        exhaustion (which doesn't clear just because a process restarted)
        keeps being respected across restarts instead of hammering a
        provider that's still actually exhausted. Use this explicitly (e.g.
        from a shell) if you know an underlying issue was fixed and want to
        stop waiting out a cooldown."""

        if provider_name is None:
            redis_conn.delete(self.REDIS_KEY)
            return
        all_health = self._read_all()
        all_health.pop(provider_name, None)
        self._write_all(all_health)

    def ordered_candidates(self, provider_names: list[str]) -> list[str]:
        """Available providers only, in the exact order given by
        `provider_names` — the caller's order (see inference_engine.py's
        `DEFAULT_PROVIDER_ORDER`) is a mandatory fallback priority, not a
        suggestion, so this only filters out providers currently in
        cooldown; it never reprioritizes by success rate or latency."""

        all_health = self._read_all()
        return [name for name in provider_names if all_health.get(name) is None or all_health[name].is_available()]

    def describe(self, provider_names: list[str]) -> list[dict]:
        """Per-provider diagnostic info for every name given, including ones
        never attempted yet (unlike snapshot(), which only reports providers
        that already exist as Redis entries) — used to log a complete
        picture before every inference attempt and before ever returning
        the all-unavailable failure, not just the ones already tracked."""

        all_health = self._read_all()
        described = []
        for name in provider_names:
            health = all_health.get(name)
            if health is None:
                described.append(
                    {"provider": name, "available": True, "in_cooldown": False, "cooldown_remaining_s": 0.0, "reason": "-"}
                )
                continue
            remaining = max(0.0, health.unavailable_until - time.time()) if health.unavailable_until else 0.0
            described.append(
                {
                    "provider": name,
                    "available": health.is_available(),
                    "in_cooldown": not health.is_available(),
                    "cooldown_remaining_s": round(remaining, 1),
                    "reason": health.last_error or "-",
                }
            )
        return described

    def snapshot(self) -> dict:
        all_health = self._read_all()
        return {
            name: {
                "status": health.status.value,
                "available": health.is_available(),
                "unavailable_for_s": (
                    round(max(0.0, health.unavailable_until - time.time()), 1) if health.unavailable_until else 0
                ),
                "last_error": health.last_error,
                "total_calls": health.total_calls,
                "success_rate": round(health.success_rate, 3),
                "average_latency_ms": round(health.average_latency_ms, 1),
            }
            for name, health in all_health.items()
        }


def format_provider_report(described: list[dict]) -> str:
    """Renders describe()'s output as the human-readable block logged
    before every inference attempt and before the all-unavailable failure:

        Provider: groq
        Available: Yes
        Cooldown: No
        Reason: -
    """

    lines = []
    for entry in described:
        lines.append(f"Provider: {entry['provider']}")
        lines.append(f"Available: {'Yes' if entry['available'] else 'No'}")
        cooldown = (
            f"Yes (expires in {entry['cooldown_remaining_s']:.0f}s)" if entry["in_cooldown"] else "No"
        )
        lines.append(f"Cooldown: {cooldown}")
        lines.append(f"Reason: {entry['reason'][:200] if entry['reason'] != '-' else '-'}")
        lines.append("")
    return "\n".join(lines)


provider_health = ProviderHealthTracker(
    quota_cooldown_seconds=settings.PROVIDER_QUOTA_COOLDOWN_SECONDS,
    rate_limit_cooldown_seconds=settings.PROVIDER_RATE_LIMIT_COOLDOWN_SECONDS,
    unavailable_cooldown_seconds=settings.PROVIDER_UNAVAILABLE_COOLDOWN_SECONDS,
)
