import re
import warnings

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Matches the scheme of a MySQL SQLAlchemy URL, with or without a DB-API
# driver suffix (e.g. "mysql://", "mysql+pymysql://", "mysql+aiomysql://").
_MYSQL_SCHEME_RE = re.compile(r"^mysql(\+\w+)?://")

# Hard product ceilings, not just defaults — a normal research request must
# never be able to run longer than this, full stop (see
# Settings.RESEARCH_JOB_TIMEOUT_SECONDS/RESEARCH_TIME_BUDGET_SECONDS below).
# Deliberately plain module constants, not themselves Settings fields:
# both this project's local .env and (almost certainly, since it was set up
# the same way) Railway's production environment variables still carry the
# old pre-120s-budget values (RESEARCH_JOB_TIMEOUT_SECONDS=1800,
# LLM_REQUEST_TIMEOUT_SECONDS=60 — confirmed present in backend/.env).
# Reading Settings fields directly (unclamped) would silently let that
# stale environment configuration reintroduce the exact unbounded-runtime
# bug this pass exists to fix, on a project where updating a real deployed
# environment's variables isn't always immediate. Clamping the *validated*
# value here (rather than failing startup with a validation error) fails
# safe: the app still boots and honors the product's hard 120s ceiling even
# against a not-yet-updated .env/deployment, instead of crash-looping.
_RESEARCH_JOB_TIMEOUT_HARD_MAX_SECONDS = 120
_LLM_REQUEST_TIMEOUT_HARD_MAX_SECONDS = 30


def _clamp(value: int, hard_max: int, field_name: str) -> int:
    if value > hard_max:
        warnings.warn(
            f"Settings.{field_name}={value} exceeds the hard product ceiling of "
            f"{hard_max}s and has been clamped to {hard_max}. Update the environment "
            f"variable to silence this warning.",
            stacklevel=2,
        )
        return hard_max
    return value


class Settings(BaseSettings):

    # ---- Application ----
    APP_NAME: str = "DeepLens API"
    APP_VERSION: str = "0.2.0-beta"
    # Fail-safe default is False (quieter, production-appropriate logging).
    # Local development's own .env explicitly sets this True, so this only
    # changes behavior for a deployment that forgets to set DEBUG at all.
    DEBUG: bool = False

    # ---- Search ----
    TAVILY_API_KEY: str

    # ---- LLM Providers ----
    GROQ_API_KEY: str = ""
    # llama-3.3-70b-versatile (the previous default) has been retired from
    # Groq's catalog — verified live against this project's own API key:
    # every call returned a real 404 "model_not_found", not a 429/quota
    # error, confirming (per this task's explicit requirement to check
    # independently rather than assume) that Groq quota exhaustion was NOT
    # what crashed the worker; this was a separate, pre-existing config bug
    # that silently wasted Groq's slot in the fallback chain on every run
    # (fails fast, ~instant, so not itself a source of hangs, but Groq was
    # never actually usable). openai/gpt-oss-120b is Groq's current
    # comparable flagship general-purpose chat model and is confirmed
    # working against this key.
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-large-latest"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    # Ollama needs a reachable local model runtime, which is real for local
    # development but doesn't exist on typical production hosts (no
    # persistent local Ollama server). Defaults to True so local dev is
    # unaffected; production deployments should explicitly set this False so
    # the fallback chain is Groq -> Mistral -> Gemini, never attempting a
    # local Ollama call that has nothing to connect to.
    ENABLE_OLLAMA: bool = True

    # None of the LLM SDKs (groq/google-genai/mistralai/ollama) set a
    # request timeout by default — a stalled connection to any one of them
    # hangs forever and defeats InferenceEngine's provider failover, which
    # only moves to the next provider once generate() actually returns.
    # Reproduced live: a Groq call hung >12 minutes with zero response,
    # blocking the whole research pipeline. Applied to every provider's
    # HTTP client at construction time.
    #
    # Lowered from 60s to 20s as part of the 120s total research budget
    # (see RESEARCH_TIME_BUDGET_SECONDS below): InferenceEngine tries its
    # candidates sequentially on failure (groq -> mistral -> gemini in
    # production), so a single generate() call's worst case is roughly
    # num_candidates * this timeout before it gives up entirely. At the old
    # 60s default that worst case alone (up to 180s for three cloud
    # providers all hanging to their timeout) already exceeded the whole
    # research budget on ONE of several LLM calls a run makes. 20s is still
    # generous for Groq/Gemini/Mistral's typical multi-second response time.
    LLM_REQUEST_TIMEOUT_SECONDS: int = 20

    @field_validator("LLM_REQUEST_TIMEOUT_SECONDS")
    @classmethod
    def _cap_llm_request_timeout(cls, v: int) -> int:
        return _clamp(v, _LLM_REQUEST_TIMEOUT_HARD_MAX_SECONDS, "LLM_REQUEST_TIMEOUT_SECONDS")

    # Tavily has no default timeout applied by this codebase before now —
    # its SDK's own default is 60s. search_agent.search() calls it once per
    # generated query (3, sequentially), so an unbounded/slow Tavily
    # response could alone consume more than the entire 120s research
    # budget. Passed explicitly to TavilyClient.search(timeout=...).
    SEARCH_REQUEST_TIMEOUT_SECONDS: int = 15
    # Ollama runs inference locally on CPU, which is legitimately much
    # slower than a cloud API call for the same prompt length — gets its
    # own, longer timeout rather than sharing the cloud providers' budget.
    OLLAMA_REQUEST_TIMEOUT_SECONDS: int = 180

    # How long InferenceEngine skips a provider after classifying a failure
    # from it (see app/providers/llm/health.py) — a provider's own stated
    # retry delay is used instead when the error text includes one (e.g.
    # Gemini's `retryDelay`), these are just the fallback when it doesn't.
    # Quota exhaustion (daily caps) gets a long cooldown since it won't
    # clear until the provider's own reset window; a bare rate limit is
    # usually transient and clears quickly; a generic/connection failure
    # sits in between.
    PROVIDER_QUOTA_COOLDOWN_SECONDS: int = 3600
    PROVIDER_RATE_LIMIT_COOLDOWN_SECONDS: int = 60
    PROVIDER_UNAVAILABLE_COOLDOWN_SECONDS: int = 300

    # ---- Vector memory (ChromaDB) ----
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    # Chroma Cloud (production): when CHROMA_API_KEY is set, ChromaStore
    # connects to Chroma Cloud instead of the local on-disk PersistentClient
    # above — local filesystem storage doesn't survive a redeploy and isn't
    # shared between the API and worker services. Left empty by default so
    # local development is completely unaffected.
    CHROMA_API_KEY: str = ""
    CHROMA_TENANT: str = ""
    CHROMA_DATABASE: str = ""

    # ---- Database (MySQL) ----
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3307/deeplens"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    @field_validator("DATABASE_URL")
    @classmethod
    def _force_async_driver(cls, v: str) -> str:
        """Some MySQL hosts (e.g. Railway's MySQL plugin) hand out a bare
        `mysql://` URL with no DB-API driver in the scheme. create_async_engine
        needs an explicit async driver — without one it silently falls back
        to the sync `mysqldb` (mysqlclient) dialect, which isn't installed
        and isn't async-capable, crashing on startup with
        `ModuleNotFoundError: No module named 'MySQLdb'`. Normalize here so
        DATABASE_URL is always usable with create_async_engine regardless of
        which driver (if any) the source URL specified."""
        return _MYSQL_SCHEME_RE.sub("mysql+aiomysql://", v, count=1)

    # ---- Redis / Task Queue ----
    REDIS_URL: str = "redis://localhost:6380/0"
    RESEARCH_QUEUE_NAME: str = "research"
    # This used to be 1800s (30 minutes), justified at the time by the
    # reflection loop's up-to-3-iteration ceiling. That is no longer this
    # project's target: a normal research request must complete in <=120s,
    # and one that can't must fail cleanly rather than occupy a worker for
    # up to half an hour. 120 is now the literal, product-required hard
    # maximum for a research request — enforced here via RQ's own
    # SIGALRM-based job timeout (rq.timeouts.UnixSignalDeathPenalty, real on
    # Railway's Linux containers), which is a genuine OS-level interrupt: it
    # fires even if a single blocking call inside a node (an LLM request, a
    # source fetch) is still in progress, which WorkflowManager's own
    # cooperative RESEARCH_TIME_BUDGET_SECONDS check below cannot do since
    # it only runs between node boundaries. This is the backstop of last
    # resort; RESEARCH_TIME_BUDGET_SECONDS is set lower so the pipeline's
    # own graceful exit has a real chance to win first in the common case.
    RESEARCH_JOB_TIMEOUT_SECONDS: int = 120

    @field_validator("RESEARCH_JOB_TIMEOUT_SECONDS")
    @classmethod
    def _cap_research_job_timeout(cls, v: int) -> int:
        return _clamp(v, _RESEARCH_JOB_TIMEOUT_HARD_MAX_SECONDS, "RESEARCH_JOB_TIMEOUT_SECONDS")

    # Cooperative wall-clock budget checked by WorkflowManager between every
    # LangGraph node (including before letting the reflection loop start
    # another iteration) — set below RESEARCH_JOB_TIMEOUT_SECONDS so a
    # normal run has time to exit with a clear, specific "exceeded time
    # budget" ResearchTimeoutError and a clean database write before RQ's
    # own harder SIGALRM deadline would otherwise fire and interrupt
    # mid-call. Not a substitute for the RQ-level timeout above — a single
    # node that blocks past this value in one call (e.g. every configured
    # LLM provider hanging to its own timeout) can only be caught by that
    # outer, OS-level deadline, not by a check that only runs between nodes.
    RESEARCH_TIME_BUDGET_SECONDS: int = 100

    @field_validator("RESEARCH_TIME_BUDGET_SECONDS")
    @classmethod
    def _cap_research_time_budget(cls, v: int, info) -> int:
        # Must stay strictly below the (already-clamped) RQ job timeout, or
        # the cooperative check could never win the race against RQ's own
        # SIGALRM — leaving every over-budget run to end with RQ's generic
        # "Task exceeded maximum timeout value" instead of this project's
        # own clearer ResearchTimeoutError message.
        job_timeout = info.data.get("RESEARCH_JOB_TIMEOUT_SECONDS", _RESEARCH_JOB_TIMEOUT_HARD_MAX_SECONDS)
        return _clamp(v, max(1, job_timeout - 10), "RESEARCH_TIME_BUDGET_SECONDS")

    # WorkflowManager's reflection-loop ceiling (previously hardcoded to 3 in
    # WorkflowManager.__init__, with no awareness of the time budget at all).
    # Reproduced live, repeatedly, against this project's own 100s budget:
    # the reflection agent asks for a second iteration on the large majority
    # of queries tried during this pass — including trivial ones ("What is
    # the capital of Japan?") — and one full additional iteration
    # (retrieval -> writer -> verification -> rewrite -> citation ->
    # reflection again) reliably costs another 40-70s on top of an already
    # 70-90s first pass, blowing the 120s hard maximum on what should be the
    # common case, not the exception. 1 means the workflow always completes
    # in a single pass regardless of the reflection agent's verdict —
    # should_continue() forces approval once iteration >= max_iterations —
    # while still computing and storing that verdict (visible in the
    # returned quality_report/reflection data) rather than hiding it. This
    # is a real, deliberate quality/reliability tradeoff, not a
    # side-effect: a normal request reliably finishing once beats an
    # unreliable chance at a "better" report across two passes that often
    # doesn't finish at all.
    RESEARCH_MAX_ITERATIONS: int = 1

    # Retrieval Node runs one embed-and-rerank cycle (including a real
    # cross-encoder inference call) per planner-generated task — a
    # comprehensive query can produce 9-14+ tasks with no cap before this.
    # Reproduced live in a container reproducing the ~1GB production limit:
    # even after every other tightening in this section, memory climbed
    # steadily across repeated retrieval tasks and was SIGKILLed partway
    # through task 7-8 of 9, plateauing around 91-92% just before tipping
    # over. Capping how many of the planner's tasks actually drive a
    # retrieval cycle bounds this node's own total work the same way
    # MAX_SOURCES_FOR_CHUNKING bounds Chunking's — the report's structure
    # (state["tasks"]) still reflects everything the planner produced; only
    # how many get their own dedicated retrieval pass is capped.
    MAX_RETRIEVAL_TASKS: int = 3

    # ---- Research pipeline resource limits ----
    # Chunking Node (app/workflows/nodes.py) downloads full source pages in
    # parallel and runs local embedding/cross-encoder models, all inside the
    # RQ work-horse process. Reproduced live in production: the work-horse
    # was SIGKILLed (OOM) immediately after Ranking, mid-Chunking, on a
    # worker container with a ~1GB memory limit. These bound peak memory for
    # that container; conservative enough there, generous enough not to
    # change local dev behavior meaningfully (this dev machine is also
    # memory-constrained per CLAUDE.md, so lower concurrency helps there too).
    #
    # First pass (EXTRACTION_WORKERS=2, MAX_SOURCE_CONTENT_CHARS=20000, model
    # preloading in app/worker.py) measurably helped — peak worker memory
    # dropped from ~98.5% to ~92% of the container limit — but two more
    # SIGKILLs still reproduced live in production immediately after that
    # deploy, both again mid-Chunking. That's direct evidence the ~1GB
    # container's baseline (torch + transformers + langgraph + chromadb + two
    # preloaded local models, all resident before any job-specific work even
    # starts) leaves too little headroom for the first pass's job-specific
    # allowance alone. Tightened further here rather than raising the
    # container's memory limit, per the fix priority this was built against:
    # reduce concurrency and source volume before reaching for more memory.
    #
    # Second pass (this pass): EXTRACTION_WORKERS=1 and deferred
    # cross-encoder loading (see app/search/cross_encoder.py) still wasn't
    # enough — SIGKILLs kept reproducing mid-Chunking at ~99% of the
    # container limit. Tightened further again: fewer sources, less text per
    # source, and a hard byte cap on the raw download itself (see
    # app/search/content_extractor.py's MAX_RAW_HTML_BYTES) rather than only
    # truncating after a potentially multi-MB page was already fully read
    # into memory. Combined with the 120s total research budget below,
    # which bounds how long Chunking (and every other node) is even allowed
    # to keep accumulating memory before the run is cut off regardless.
    EXTRACTION_WORKERS: int = 1
    MAX_SOURCES_FOR_CHUNKING: int = 2
    # Caps extracted text per source before it flows into chunking/embedding —
    # a handful of oversized pages (long-form articles, PDF-derived dumps)
    # downloaded concurrently was part of the peak-memory spike.
    MAX_SOURCE_CONTENT_CHARS: int = 4000

    # Third pass: even after replacing sentence-transformers/torch with
    # fastembed (ONNX Runtime) for both embedding and reranking — which cut
    # baseline worker memory from ~74-98% of the 1GB container down to
    # ~48%, measured live — a real container reproducing this exact limit
    # still SIGKILLed, later in the pipeline this time (during Retrieval
    # Node's first cross-encoder rerank call, right as its ONNX model
    # finished loading, rather than during Chunking's embedding step as
    # before). The cross-encoder's own model files/session initialization
    # has a real, separate memory cost on top of the embedder's, and both
    # models' weights are resident simultaneously by the time reranking
    # starts. Tightened source volume further here for the same reason as
    # the first two passes: fewer, smaller chunks resident in memory by the
    # time the cross-encoder loads.

    # ---- Security ----
    # No default on purpose: every environment must set its own signing key
    # rather than silently inherit one, the same way TAVILY/GEMINI keys work.
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # ---- Email ----
    # SMTP_HOST empty = no real SMTP configured; EmailSender (core/email.py)
    # falls back to logging the message (including reset/verify links)
    # instead of failing, so auth flows are fully usable in dev without
    # real credentials only the deployer can obtain.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@deeplens.local"
    SMTP_USE_TLS: bool = True
    # smtplib.SMTP() has no timeout by default — same class of bug as the LLM
    # providers (app/providers/llm/*): an unreachable or slow SMTP host would
    # hang the request indefinitely instead of failing. Applied at the
    # connection call in app/core/email.py.
    SMTP_TIMEOUT_SECONDS: int = 30

    # ---- Frontend ----
    # Used to build links (password reset, email verification) sent by email.
    FRONTEND_URL: str = "http://localhost:3000"
    # Comma-separated list of origins allowed to call the API from a browser
    # (CORS). Defaults to the local Next.js dev server; add production
    # frontend origins here, don't widen this to "*" once cookies/credentials
    # are ever introduced.
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """The app runs on the async `aiomysql` driver; Alembic and the
        research pipeline worker (agents/workflows/nodes.py — synchronous
        code, run in an RQ worker process rather than on the request
        thread) use this `pymysql`-backed equivalent instead. Derived by
        re-normalizing the scheme (not a literal "+aiomysql" substring
        replace) so it's correct even if DATABASE_URL's validator above
        had to rewrite the driver from something else."""
        return _MYSQL_SCHEME_RE.sub("mysql+pymysql://", self.DATABASE_URL, count=1)

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
