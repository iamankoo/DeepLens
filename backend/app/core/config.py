import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Matches the scheme of a MySQL SQLAlchemy URL, with or without a DB-API
# driver suffix (e.g. "mysql://", "mysql+pymysql://", "mysql+aiomysql://").
_MYSQL_SCHEME_RE = re.compile(r"^mysql(\+\w+)?://")


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
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

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
    LLM_REQUEST_TIMEOUT_SECONDS: int = 60
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
    # RQ's own default job timeout is 180s (rq.queue.Queue.DEFAULT_TIMEOUT) —
    # far too short for this pipeline, which can legitimately run 10-15+
    # minutes across multiple nodes and up to 3 reflection iterations.
    # Reproduced live: a real run was killed by RQ with "Task exceeded
    # maximum timeout value (180 seconds)" mid-pipeline. Always pass this
    # explicitly to research_queue.enqueue(..., job_timeout=...) — never
    # rely on RQ's default for this queue.
    RESEARCH_JOB_TIMEOUT_SECONDS: int = 1800

    # ---- Research pipeline resource limits ----
    # Chunking Node (app/workflows/nodes.py) downloads full source pages in
    # parallel and runs local embedding/cross-encoder models, all inside the
    # RQ work-horse process. Reproduced live in production: the work-horse
    # was SIGKILLed (OOM) immediately after Ranking, mid-Chunking, on a
    # worker container with a ~1GB memory limit. These bound peak memory for
    # that container; conservative enough there, generous enough not to
    # change local dev behavior meaningfully (this dev machine is also
    # memory-constrained per CLAUDE.md, so lower concurrency helps there too).
    EXTRACTION_WORKERS: int = 2
    MAX_SOURCES_FOR_CHUNKING: int = 8
    # Caps extracted text per source before it flows into chunking/embedding —
    # a handful of oversized pages (long-form articles, PDF-derived dumps)
    # downloaded concurrently was part of the peak-memory spike.
    MAX_SOURCE_CONTENT_CHARS: int = 20000

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
