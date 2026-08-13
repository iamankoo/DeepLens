from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ---- Application ----
    APP_NAME: str = "DeepLens API"
    APP_VERSION: str = "0.2.0-beta"
    DEBUG: bool = True

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

    # ---- Database (MySQL) ----
    DATABASE_URL: str = "mysql+aiomysql://root:password@localhost:3307/deeplens"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ---- Redis / Task Queue ----
    REDIS_URL: str = "redis://localhost:6380/0"
    RESEARCH_QUEUE_NAME: str = "research"

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

    # ---- Frontend ----
    # Used to build links (password reset, email verification) sent by email.
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """The app runs on the async `aiomysql` driver; Alembic and the
        research pipeline worker (agents/workflows/nodes.py — synchronous
        code, run in an RQ worker process rather than on the request
        thread) use this `pymysql`-backed equivalent instead."""
        return self.DATABASE_URL.replace("+aiomysql", "+pymysql")


settings = Settings()
