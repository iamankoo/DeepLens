# CLAUDE.md

## Project Overview

- **Purpose**: DeepLens is an AI-powered Deep Research Engine. It takes a user query and runs it through a structured multi-agent pipeline (Planner → Search → Source Ranking → Retrieval/Chunking → Writer → Verification/Rewrite → Citation → Reflection) to produce a structured, cited research report, run as a background job and polled for status. Current code version is `0.2.0-beta` (README says `v0.1.0-alpha` — the README is stale; trust the code).
- **Tech stack**: Python — FastAPI, LangGraph, LangChain-core, Pydantic v2/pydantic-settings, Tavily (web search), SQLAlchemy 2.0 + Alembic against MySQL (async via `aiomysql`, sync via `pymysql` — see Database below), Redis + RQ for the research job queue, ChromaDB (long-term memory), multi-provider LLM layer (Gemini, Groq, Mistral, Ollama), sentence-transformers for embeddings, pytest/pytest-asyncio, ruff/black. `frontend/` is a Next.js 15 (App Router) + React 19 + TypeScript app — see Frontend below; auth is fully wired end-to-end, the rest of the UI (app shell, research pages, document upload) is still being built out.
- **Main architecture**: Layered, provider-abstracted, agentic workflow: API layer (FastAPI routers) → Service layer (`research_service.py`, enqueues a job and returns immediately) → Job layer (`app/jobs/research_job.py`, run by an RQ worker) → Workflow layer (LangGraph `StateGraph`) → Agent layer (`agents/`, each pairing a prompt + LLM call) → Provider layer (pluggable LLM/search providers) → Domain support modules (`search/` ranking & retrieval, `citations/`, `intelligence/` evidence scoring, `memory/` ChromaDB, `rewrite/`). The core pipeline includes a conditional reflection loop that can iterate back to retrieval rather than being strictly linear.
- **Important folders** (all under `backend/app/`):
  - `agents/` — planner, query_refinement, reflection, research, search, source_ranker, writer
  - `providers/llm/` — base/gemini/groq/mistral/ollama + `manager.py`/`registry.py`
  - `providers/search/` — base + `tavily_provider.py` + `manager.py`
  - `workflows/` — `state.py` (`ResearchState`), `nodes.py`, `research_workflow.py`, `workflow_manager.py`
  - `prompts/` — per-agent prompt templates, isolated from agent logic
  - `citations/`, `intelligence/`, `memory/` (ChromaDB store + embedding provider), `rewrite/`, `search/` (chunking/ranking/retrieval)
  - `db/` — SQLAlchemy models (`db/models/`), sync+async engines/sessions (`db/session.py`), repositories (`db/repositories/`)
  - `queue/` — `connection.py` (Redis connection + RQ `research_queue`, both built from `Settings`)
  - `jobs/` — `research_job.py`, the function the RQ worker actually executes
  - `worker.py` — the RQ worker entry point (`python -m app.worker`); picks `SimpleWorker` on Windows automatically, see Known Gotchas below
  - `core/security.py` — password hashing (bcrypt), JWT access tokens, opaque (hashed-at-rest) refresh tokens
  - `api/v1/deps.py` — `get_current_user`, `get_current_user_optional`, `require_role(*roles)` — the auth/RBAC dependencies every protected or attribution-aware endpoint uses
  - `backend/tests/` — current, maintained pytest suite; `backend/old_tests/` — **deprecated, do not extend**
- **Entry points**:
  - API: `backend/app/main.py` (FastAPI app, mounts `api_router` under `/api/v1`), run via `uvicorn app.main:app --reload` from `backend/`. `POST /api/v1/research` enqueues a job and returns `202` immediately with the run's id/status; poll `GET /api/v1/research/{id}` for progress and the final report, or `GET /api/v1/research` for history. Auth is optional on this endpoint (see Authentication below) — an authenticated request attaches `user_id`, an anonymous one still works.
  - Worker: `python -m app.worker` from `backend/` — must be running for queued research to ever execute; the API alone will accept requests but they'll sit at `pending` forever without a worker.
  - Workflow: `research_workflow.py`'s compiled graph, entry node `"planner"`, invoked by `app/jobs/research_job.py` inside the worker process.

## Database

- MySQL, via SQLAlchemy 2.0 + Alembic. Two engines exist on purpose, not by accident: `db_manager.engine` (async, `aiomysql`) backs new async endpoints (the `GET` history/detail routes); `db_manager.sync_engine` (sync, `pymysql`) backs the still-synchronous research pipeline and the RQ worker, which can't use an async session without an async rewrite of `agents/`/`workflows/` (that's a bigger, separate change, not bundled into the queue work). Alembic also runs on the sync URL — see `Settings.SYNC_DATABASE_URL`, which derives it from `DATABASE_URL` by swapping the driver.
- `pool_pre_ping=True` is deliberately **not** set on the async engine — in this SQLAlchemy 2.0.49 environment it throws `TypeError` on every checkout of a pooled (non-fresh) connection, reproduced with both `aiomysql` and `asyncmy`. It's fine on the sync engine. Don't re-add it to the async engine without re-testing against a live MySQL first.
- Local dev DB/Redis: `docker/docker-compose.yml` runs MySQL on host port **3307** and Redis on host port **6380** — not the defaults (3306/6379), because this dev machine already has an unrelated native MySQL on 3306 and another project's Redis container on 6379. `DATABASE_URL`/`REDIS_URL` in `.env.example` already point at the non-default ports; don't "fix" them back to 3306/6379 without checking what's actually running there first.
- Migrations: `alembic revision --autogenerate -m "..."` then `alembic upgrade head`, from `backend/`. Autogenerated `downgrade()` for a table with both an FK and an index on the FK'd column needs manual adjustment on MySQL — it drops the index before the constraint that depends on it, which MySQL rejects (fine on Postgres/SQLite). Fix by removing that specific `drop_index` call and letting `drop_table` remove it along with the constraint.

## Task Queue

- RQ (Redis Queue), not Celery or arq — the whole pipeline is synchronous Python, so RQ's plain-function worker model needed zero changes to `agents/`/`workflows/`; Celery's broker/backend/routing machinery would be pure overhead for one queue and one job type, and arq is async-first which doesn't fit code that isn't.
- **Always start the worker via `python -m app.worker`**, never `rq worker research` directly — the bare CLI defaults to `redis://localhost:6379`, which on this machine is a *different project's* Redis container, so jobs get enqueued into one Redis and the worker listens on another and nothing ever runs, silently. `app/worker.py` builds its connection from `Settings.REDIS_URL` so this can't happen.
- **On Windows, the worker must be `rq.worker.SimpleWorker`**, not the default `Worker` — the default forks a child process per job via `os.fork()`, which doesn't exist on Windows; jobs get accepted into the queue but never dequeued, with no error. `app/worker.py` already branches on `sys.platform` for this; don't hardcode `Worker` in new code that spawns workers.
- Job lifecycle: `research_service.create_research` creates a `ResearchRun` row (`status=pending`) and enqueues `app.jobs.research_job.run_research_job(research_id, query)` in the same call, then returns immediately. The job function transitions the row through `running` → `completed`/`failed`, persisting `report`/`quality_score`/`iteration` or `error`.

## Authentication

- JWT access tokens (30 min default, `Settings.ACCESS_TOKEN_EXPIRE_MINUTES`) + opaque refresh tokens (7 day default, `Settings.REFRESH_TOKEN_EXPIRE_DAYS`). Refresh tokens are random (`secrets.token_urlsafe`), not JWTs — only their SHA-256 hash is stored (`refresh_tokens` table), so a leaked DB row can't be replayed as a bearer credential, and they support real server-side revocation (JWTs alone don't, short of a blocklist).
- Refresh rotation: every `POST /api/v1/auth/refresh` call revokes the token it was given and issues a new pair. A refresh token is single-use — reusing one after it's been redeemed returns `401`. This is deliberate (limits the blast radius of a leaked refresh token), not a bug.
- Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/verify-email`, `POST /auth/resend-verification`. Passwords are bcrypt-hashed via `run_in_threadpool` (hashing is CPU-bound, ~100-300ms — don't call `hash_password`/`verify_password` directly from an `async def` endpoint without that wrapper, it'll block the event loop).
- Password reset and email verification share one `email_tokens` table (`EmailToken`, `purpose` = `password_reset` | `email_verification`) rather than two near-identical tables — same hashed-at-rest, single-use, expiring pattern as refresh tokens, via `core/security.py`'s `generate_email_token`/`hash_email_token`. `forgot-password` and `resend-verification` always return the same generic message regardless of whether the email exists, at the endpoint layer (`AuthService.forgot_password`/`resend_verification` return `None` either way) — never make either of those leak account existence.
- Resetting a password revokes every refresh token for that user (`RefreshTokenRepository.revoke_all_for_user`) — a leaked password shouldn't leave a still-valid session behind. Verified live: a refresh token issued before a reset correctly 401s afterward.
- `core/email.py`'s `EmailSender` is the only place that sends mail. With `SMTP_HOST` unset (the local-dev default) it logs the message — including the actual reset/verify link — instead of sending it, so the full flow is testable without real SMTP credentials; this is a real fallback code path, not a mock. Set `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` to an actual relay to send for real.
- RBAC: `UserRole` (`user`/`admin`) on the `User` model; `require_role(*roles)` in `api/v1/deps.py` is the dependency factory for role-gated endpoints. No endpoint uses it yet — there's no admin-only functionality built (that's Phase 6, the admin dashboard); it exists now as infrastructure ready for that.
- `POST /api/v1/research` uses `get_current_user_optional`, not `get_current_user` — research creation is **not** gated behind login. An authenticated request attaches `user_id` to the `ResearchRun` for history/ownership; an anonymous request still works exactly as before. Whether research should require an account is a product decision, not made here — flip that one dependency if/when that's decided, everything else (the `user_id` column, the attribution logic) is already in place either way.

## Frontend

- Next.js 15 (App Router, no `src/` dir) + React 19 + TypeScript, scaffolded with the shadcn/ui `base-nova` style, which is built on **Base UI** (`@base-ui/react`), not Radix — components use base-ui's `render` prop for polymorphic rendering (e.g. `<Button render={<Link href="/x" />}>`), not Radix's `asChild`. `components/ui/*` are generated by `npx shadcn@latest add <name>` from `frontend/` — don't hand-edit their internals beyond what the CLI generates; extend via composition instead.
- **shadcn's `form` registry item is now an empty stub in this version** (confirmed via `npx shadcn@latest view form`, prints `{"name": "form", "type": "registry:ui"}` with no files) — it's been replaced by a `field` component (`components/ui/field.tsx`: `Field`, `FieldLabel`, `FieldError`, `FieldGroup`, etc.) used together with React Hook Form's own `<Controller>` directly, not a `<Form>` wrapper. Pattern used throughout `components/auth/*`: `useForm` + `zodResolver`, then `<Controller name=".." control={form.control} render={({ field, fieldState }) => <Field data-invalid={fieldState.invalid}>...</Field>} />`. Don't try to `shadcn add form` again expecting it to work — it silently writes nothing.
- State/data layers: Zustand (`stores/auth-store.ts`, `persist` middleware, key `deeplens-auth`, in `localStorage`) for client auth state; TanStack Query (`providers/query-provider.tsx`) for server state, wrapped around mutations/queries in `hooks/use-auth.ts`. Zod schemas mirroring backend Pydantic schemas live in `lib/validations/`.
- `lib/api-client.ts` is the single Axios instance (`apiClient`) — it attaches `Authorization: Bearer <accessToken>` from the Zustand store on every request and transparently refreshes on a 401 (deduped via a shared in-flight promise, since refresh tokens are single-use/rotating server-side — see Authentication above). `/auth/*` requests are excluded from the retry-on-401 loop so a bad-password login isn't misinterpreted as an expired token. `services/*-service.ts` files are thin typed wrappers over `apiClient` per backend resource (e.g. `auth-service.ts`) — add new ones the same way rather than calling `apiClient` directly from components.
- **Auth/session guard is client-side, not middleware**: tokens live in `localStorage` via zustand/persist, which Next's edge middleware cannot read, so there is no `middleware.ts` gating routes. Instead, `app/(app)/layout.tsx` wraps protected routes in `components/auth/require-auth.tsx`, which waits for store hydration (`isHydrated`), requires a valid `/auth/me` response (via `useCurrentUser` in `hooks/use-auth.ts`), and redirects to `/login` otherwise; it also accepts an `allowedRoles` prop for RBAC-gated routes (infrastructure ready, not yet used by any page). `app/(auth)/layout.tsx` does the inverse — redirects an already-authenticated visitor away from `/login`/`/register`/etc. to `/dashboard`.
- Full auth UI exists under `app/(auth)/{login,register,forgot-password,reset-password,verify-email}` (shared visual shell: `components/auth/auth-shell.tsx`) and calls the real backend endpoints from Authentication above — no mock data or placeholder auth anywhere. `reset-password`/`verify-email` read `?token=` from the URL (matches the links `EmailSender` logs/sends) via a small client component wrapped in `<Suspense>` (required by Next 15 for `useSearchParams` in a page that's otherwise statically rendered).
- `app/(app)/dashboard/page.tsx` is currently a minimal placeholder (proves the guard + session flow end-to-end) — the real sidebar/topnav app shell around it is later, separately scoped work; don't mistake it for the finished dashboard.
- `next.config.ts` sets `outputFileTracingRoot` explicitly — this repo lives inside a larger workspace directory containing many unrelated sibling projects, one of which has a stray `package-lock.json` at the workspace root that Next.js would otherwise misdetect as the monorepo root.

## Development Standards

- Production-ready code only in `backend/app/` — the old top-level `backend/{agents,core,db,models,routers,schemas,services,tools,utils,workflows}/` scaffolding (empty, duplicating names under `app/`) has been removed; always use the `backend/app/` package.
- **Provider abstraction pattern is mandatory**: any new LLM or search backend must implement the relevant `base.py`/`base_provider.py` interface and register via the corresponding `manager.py`/`registry.py`, following the existing Gemini/Groq/Mistral/Ollama and Tavily examples. Don't call a provider SDK directly from agent code.
- **Prompt isolation**: prompt text belongs in `app/prompts/<name>.py`, never inline in agent code.
- Agent = prompt + LLM provider + schema — each agent pairs a `schemas/` request/response model with a `prompts/` template and calls into `providers/llm/`.
- Workflow nodes are pure functions in `app/workflows/nodes.py`; state is centralized in `app/workflows/state.py` (`ResearchState`) — don't scatter workflow state elsewhere.
- Module-level singleton export convention: expose a ready-to-use lowercase instance (e.g. `writer_agent`, `research_service`, `settings`, `db_manager`, `research_queue`) rather than requiring callers to instantiate classes — follow this for new modules.
- Application-level failures use the `app/core/exceptions.py` hierarchy (`DeepLensError` → `LLMProviderError`, `OutputParsingError`), caught by typed handlers in `main.py` (502 for upstream provider/parsing failures, 500 for other app errors) — raise these instead of bare `Exception` so failures get a meaningful HTTP status instead of a generic 500.
- Logging goes through `app/core/logger.py`'s `logger`, not `print()` — it supports `extra={...}` for structured context (rendered as `key=value` suffixes) and respects `settings.DEBUG` for level. The core pipeline (`nodes.py`, `workflow_manager.py`, `research_agent.py`) already follows this; some peripheral modules (`search_agent.py`, `cross_encoder.py`, etc.) still use `print()` and haven't been converted yet — match whichever convention the file you're editing already uses, but use `logger` for anything new.

## Coding Rules

- Match existing style: Pydantic `BaseSettings` for config (`app/core/config.py`, `case_sensitive=True`, reads from `.env`); comment-banner section dividers (e.g. `# ---- Nodes ----`) in workflow files.
- Type all Pydantic schemas; keep `schemas/` (I/O models) separate from `agents/`/`services/` (logic). ORM models live in `db/models/`, not `schemas/` — schemas are the API I/O boundary, models are the persistence boundary; don't collapse the two.
- No hardcoded secrets — all API keys come from `.env` via `Settings`.
- `requirements.txt` is UTF-16 encoded (a historical artifact, not a choice) — preserve that encoding when editing it programmatically (`open(..., encoding='utf-16')`), a plain-UTF-8 write will corrupt it for anyone who reads it normally. It's still a broad `pip freeze` of more than this project needs; trust actual imports in `app/` as ground truth over the full file contents.

## Security Rules

- Never expose `TAVILY_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `SECRET_KEY` — these are required (no defaults for Tavily/Gemini/SECRET_KEY) and must only load via `Settings`/`.env`.
- Never commit `backend/.env` (only `.env.example` is tracked).
- Validate/sanitize search-derived content before it flows into the writer/citation pipeline (untrusted web content).
- Auth exists now (see Authentication above) but is opt-in on `/research` — most endpoints are still effectively open. Don't assume request-level authorization is enforced anywhere it isn't explicitly wired via `get_current_user`/`require_role`.
- CORS is enforced via `CORSMiddleware` in `main.py`, origins from `Settings.CORS_ORIGINS_LIST` (comma-separated `CORS_ORIGINS` env var, defaults to `http://localhost:3000`). Add any real deployed frontend origin here; don't widen it to `"*"` — `allow_credentials=True` is set, and browsers reject `*` combined with credentials anyway.

## Performance Rules

- The reflection loop can re-run retrieval — avoid unbounded loops; respect the existing `should_continue` conditional-edge logic that governs when the graph terminates vs. loops back.
- Avoid redundant LLM calls across agents within one workflow run; pass extracted state forward via `ResearchState` rather than re-deriving it.
- ChromaDB-backed long-term memory (`memory/stores/chroma_store.py`) should be queried, not re-embedded, when the same content is looked up repeatedly.
- The research pipeline runs in an RQ worker now, off the API request thread — don't reintroduce synchronous, in-request execution of the full pipeline (e.g. by calling `research_agent.run()` directly from an endpoint) without a specific reason; that's the exact blocking-request problem the queue exists to avoid.

## Testing

- **pytest + pytest-asyncio**. Use `backend/tests/` (current, 11 files: chunker, citations, cross_encoder, e2e_pipeline, embeddings, evidence, ranking, reflection, retriever, rewrite, search, writer) — this is the maintained suite.
- **`backend/old_tests/` (34 files) is legacy/deprecated — do not add to it; treat `backend/tests/` as the source of truth.**
- Tests here often exercise real agent singletons (e.g. `writer_agent.generate_report(...)`) rather than mocks, meaning some tests can make live LLM/search calls — be aware of this when running the suite or adding new tests, and mock external calls where practical for new unit tests.
- Never remove existing tests in `backend/tests/`.
- No DB/queue-specific automated tests exist yet — the persistence and queue layers so far have been verified manually against a live MySQL/Redis (migration up/down/up roundtrips, repository reads/writes, `TestClient` requests including realistic pooled-connection reuse, and one full real research job through the actual worker). Adding real pytest coverage for these is tracked as later-phase work, not done yet.

## Documentation

- `docs/` contains 13 pre-created but currently **empty** doc files (`01-product-requirements.md` through `13-roadmap.md`, covering architecture, DB design, API spec, agent design, LangGraph workflow, memory system, search pipeline, deployment, testing, roadmap) — this is an intentional skeleton meant to be filled in, not duplicated with new docs elsewhere.
- README's project-structure snippet and "Current Status"/version are stale relative to the actual `app/` layout and version (`0.2.0-beta`) — update README when making structural or version changes, or at least flag the discrepancy.

## Git Workflow

- Small, logical commits per agent/provider/workflow-node change.
- Never rewrite history or force-push unless explicitly asked.
- `.gitignore` already covers `.langgraph_api/`, SQLite db files, `.env`, venvs — keep new generated artifacts (e.g. new `chroma_db/` collections) out of git unless intentionally versioned.

## Editing Behaviour

- Understand the LangGraph state machine (`workflows/research_workflow.py`, `nodes.py`, `state.py`) before modifying the research pipeline — it's the architectural core.
- Explain the plan before large refactors touching the provider abstraction or the reflection loop's termination logic.
- Preserve the provider-abstraction contract when adding a new LLM/search backend — don't special-case a new provider outside the `base.py`/`manager.py`/`registry.py` pattern.
- Ask before deleting `backend/old_tests/` (may still be useful as reference) or the empty `docs/`/`infrastructure/` scaffolding (intentional placeholders for planned work). `frontend/` is an active, real Next.js app now, not empty scaffolding — see Frontend above.
- The DB target is decided (MySQL, see Database above) — don't ask about that again, but do check before assuming ports/credentials: this dev machine has other unrelated DB/Redis containers and a native MySQL install, so "the default port" is not a safe assumption here.

## Project-Specific Guidelines

- **Commands** (from `backend/`):
  - `pip install -r requirements.txt`
  - `docker compose -f ../docker/docker-compose.yml up -d` (starts local MySQL on 3307 + Redis on 6380)
  - `alembic upgrade head` (apply migrations)
  - `uvicorn app.main:app --reload` (API; docs at `http://127.0.0.1:8000/docs`)
  - `python -m app.worker` (RQ worker — required for queued research to actually run; see Task Queue above for why the bare `rq worker` CLI doesn't work here)
  - `pytest` or `pytest tests/`
  - `ruff check .`; `black .` (no committed ruff/black config found — defaults are in use; a `.ruff_cache/` exists confirming ruff has been run)
- **Env vars** actually consumed by `Settings`: `APP_NAME`, `APP_VERSION`, `DEBUG`, `TAVILY_API_KEY` (required), `GROQ_API_KEY`/`GROQ_MODEL`, `GEMINI_API_KEY` (required)/`GEMINI_MODEL`, `MISTRAL_API_KEY`/`MISTRAL_MODEL`, `OLLAMA_BASE_URL`/`OLLAMA_MODEL`, `DATABASE_URL`/`DB_ECHO`/`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`, `REDIS_URL`/`RESEARCH_QUEUE_NAME`, `SECRET_KEY` (required, no default — every environment sets its own JWT signing key)/`JWT_ALGORITHM`/`ACCESS_TOKEN_EXPIRE_MINUTES`/`REFRESH_TOKEN_EXPIRE_DAYS`, `CORS_ORIGINS` (comma-separated browser origins allowed to call the API).
- **Frontend commands** (from `frontend/`): `npm run dev` (dev server, `http://localhost:3000`), `npm run build` / `npm run start` (production build/serve), `npx tsc --noEmit` (typecheck), `npx shadcn@latest add <component>` (pull a new shadcn/ui component — see the `form`-is-a-stub gotcha in Frontend above before reaching for that specific one). Frontend env vars: `NEXT_PUBLIC_API_URL` (backend base URL including `/api/v1`, in `frontend/.env.local`/`frontend/.env.example`) — kept synchronized the same way as the backend's `.env`/`.env.example`.
- **`.env`/`.env.example` policy**: both are kept synchronized and grouped by category (Application/Search/LLM Providers/Database/Redis/Security/...) whenever a variable is added, changed, or removed — `.env` holds real local values, `.env.example` holds the same names with placeholders only. Never hardcode a secret in source; add it to `Settings` and both env files instead.
- **Key dependencies to respect**: `langgraph` (orchestration core), `tavily-python` (only configured search backend today), `chromadb` (long-term memory), `sqlalchemy`/`alembic` (MySQL persistence), `rq`/`redis` (job queue), `pyjwt`/`bcrypt` (auth), the multi-provider LLM abstraction.
- No CI is configured yet (`.github/` is empty) — don't assume automated checks catch regressions; run `pytest`/`ruff` locally.
