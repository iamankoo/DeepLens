# CLAUDE.md

## Project Overview

- **Purpose**: DeepLens is an AI-powered Deep Research Engine. It takes a user query and runs it through a structured multi-agent pipeline (Planner → Search → Source Ranking → Retrieval/Chunking → Writer → Verification/Rewrite → Citation → Reflection) to produce a structured, cited research report. Current code version is `0.2.0-beta` (README says `v0.1.0-alpha` — the README is stale; trust the code).
- **Tech stack**: Python — FastAPI, LangGraph, LangChain-core, Pydantic v2/pydantic-settings, Tavily (web search), SQLAlchemy 2.0 + Alembic + aiosqlite (present but DB layer not yet wired up), ChromaDB (long-term memory), multi-provider LLM layer (Gemini, Groq, Mistral, Ollama), sentence-transformers for embeddings, pytest/pytest-asyncio, ruff/black. A `frontend/` folder exists but is currently empty scaffolding only — no frontend code yet.
- **Main architecture**: Layered, provider-abstracted, agentic workflow: API layer (FastAPI routers) → Service layer (`research_service.py`) → Workflow layer (LangGraph `StateGraph`) → Agent layer (`agents/`, each pairing a prompt + LLM call) → Provider layer (pluggable LLM/search providers) → Domain support modules (`search/` ranking & retrieval, `citations/`, `intelligence/` evidence scoring, `memory/` ChromaDB, `rewrite/`). The core pipeline includes a conditional reflection loop that can iterate back to retrieval rather than being strictly linear.
- **Important folders** (all under `backend/app/`):
  - `agents/` — planner, query_refinement, reflection, research, search, source_ranker, writer
  - `providers/llm/` — base/gemini/groq/mistral/ollama + `manager.py`/`registry.py`
  - `providers/search/` — base + `tavily_provider.py` + `manager.py`
  - `workflows/` — `state.py` (`ResearchState`), `nodes.py`, `research_workflow.py`, `workflow_manager.py`
  - `prompts/` — per-agent prompt templates, isolated from agent logic
  - `citations/`, `intelligence/`, `memory/` (ChromaDB store + embedding provider), `rewrite/`, `search/` (chunking/ranking/retrieval)
  - `backend/tests/` — current, maintained pytest suite; `backend/old_tests/` — **deprecated, do not extend**
- **Entry points**: `backend/app/main.py` (FastAPI app, mounts `api_router` under `/api/v1`), run via `uvicorn app.main:app --reload` from `backend/`. Workflow entry: `research_workflow.py`'s compiled graph, entry node `"planner"`. API entry: `POST /api/v1/research`.

## Development Standards

- Production-ready code only in `backend/app/` — several top-level `backend/` directories (`agents/`, `core/`, `db/`, `models/`, `routers/`, `schemas/`, `services/`, `tools/`, `utils/`, `workflows/`, all empty and duplicating names under `app/`) are abandoned/unused scaffolding; do not add code there — always use the `backend/app/` package.
- **Provider abstraction pattern is mandatory**: any new LLM or search backend must implement the relevant `base.py`/`base_provider.py` interface and register via the corresponding `manager.py`/`registry.py`, following the existing Gemini/Groq/Mistral/Ollama and Tavily examples. Don't call a provider SDK directly from agent code.
- **Prompt isolation**: prompt text belongs in `app/prompts/<name>.py`, never inline in agent code.
- Agent = prompt + LLM provider + schema — each agent pairs a `schemas/` request/response model with a `prompts/` template and calls into `providers/llm/`.
- Workflow nodes are pure functions in `app/workflows/nodes.py`; state is centralized in `app/workflows/state.py` (`ResearchState`) — don't scatter workflow state elsewhere.
- Module-level singleton export convention: expose a ready-to-use lowercase instance (e.g. `writer_agent`, `research_service`, `settings`) rather than requiring callers to instantiate classes — follow this for new modules.

## Coding Rules

- Match existing style: Pydantic `BaseSettings` for config (`app/core/config.py`, `case_sensitive=True`, reads from `.env`); comment-banner section dividers (e.g. `# ---- Nodes ----`) in workflow files.
- Type all Pydantic schemas; keep `schemas/` (I/O models) separate from `agents/`/`services/` (logic).
- No hardcoded secrets — all API keys come from `.env` via `Settings`.
- `requirements.txt` is currently a full `pip freeze` of a much broader environment (UTF-16 encoded, includes many unrelated packages like `deepface`, `tensorflow`, `pyautogui`) — **trust actual imports in `app/` as ground truth for real dependencies**, not this file; clean it up if asked to touch dependency management.

## Security Rules

- Never expose `TAVILY_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY` — these are required (no defaults for Tavily/Gemini) and must only load via `Settings`/`.env`.
- Never commit `backend/.env` (only `.env.example` is tracked) — note the existing `.env.example` mixes valid `.env` syntax with stray Python type-annotation-style lines; clean this up if you touch it, without accidentally documenting variables the `Settings` class doesn't actually read (e.g. `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL`, `SECRET_KEY` are in `.env.example` but not in the `Settings` class — flag rather than silently wire up unless asked).
- Validate/sanitize search-derived content before it flows into the writer/citation pipeline (untrusted web content).

## Performance Rules

- The reflection loop can re-run retrieval — avoid unbounded loops; respect the existing `should_continue` conditional-edge logic that governs when the graph terminates vs. loops back.
- Avoid redundant LLM calls across agents within one workflow run; pass extracted state forward via `ResearchState` rather than re-deriving it.
- ChromaDB-backed long-term memory (`memory/stores/chroma_store.py`) should be queried, not re-embedded, when the same content is looked up repeatedly.

## Testing

- **pytest + pytest-asyncio**. Use `backend/tests/` (current, 11 files: chunker, citations, cross_encoder, e2e_pipeline, embeddings, evidence, ranking, reflection, retriever, rewrite, search, writer) — this is the maintained suite.
- **`backend/old_tests/` (34 files) is legacy/deprecated — do not add to it; treat `backend/tests/` as the source of truth.**
- Tests here often exercise real agent singletons (e.g. `writer_agent.generate_report(...)`) rather than mocks, meaning some tests can make live LLM/search calls — be aware of this when running the suite or adding new tests, and mock external calls where practical for new unit tests.
- Never remove existing tests in `backend/tests/`.

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
- Ask before deleting `backend/old_tests/` (may still be useful as reference) or the empty `frontend/`/`docs/`/`infrastructure/` scaffolding (intentional placeholders for planned work).
- Ask before changing the DB layer's target (SQLAlchemy/Alembic dependencies exist but `db/` is unbuilt) — clarify whether SQLite, Postgres, or another target is intended before wiring it up, since `.env.example` hints at Postgres/Redis/Qdrant but none of that is implemented yet.

## Project-Specific Guidelines

- **Commands** (from `backend/`): `pip install -r requirements.txt`; `uvicorn app.main:app --reload` (docs at `http://127.0.0.1:8000/docs`); `pytest` or `pytest tests/`; `ruff check .`; `black .` (no committed ruff/black config found — defaults are in use; a `.ruff_cache/` exists confirming ruff has been run).
- **Env vars** actually consumed by `Settings`: `APP_NAME`, `APP_VERSION`, `DEBUG`, `TAVILY_API_KEY` (required), `GROQ_API_KEY`/`GROQ_MODEL`, `GEMINI_API_KEY` (required)/`GEMINI_MODEL`, `MISTRAL_API_KEY`/`MISTRAL_MODEL`, `OLLAMA_BASE_URL`/`OLLAMA_MODEL`. Other vars in `.env.example` (`OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL`, `SECRET_KEY`) are not yet read by code.
- **Key dependencies to respect**: `langgraph` (orchestration core), `tavily-python` (only configured search backend today), `chromadb` (long-term memory), the multi-provider LLM abstraction.
- No CI is configured yet (`.github/` is empty) — don't assume automated checks catch regressions; run `pytest`/`ruff` locally.
