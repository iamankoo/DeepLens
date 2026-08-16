"""
nodes.py — DeepLens Workflow Nodes (Production-hardened)

Performance:
  - chunking_node uses ThreadPoolExecutor for parallel URL extraction
  - ranked_sources capped at MAX_SOURCES_FOR_CHUNKING (8)
  - verification / citation use chunk_pool directly (zero re-downloads)
  - every node logs timing at DEBUG/INFO via the shared structured logger

Robustness:
  - every expensive call wrapped in try/except
  - no node ever returns None
  - reflection fail-safe prevents infinite loop
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from uuid import uuid4

from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker
from app.agents.writer_agent import writer_agent
from app.agents.reflection_agent import reflection_agent

from app.core.config import settings
from app.core.logger import logger
from app.memory.manager import memory_manager
from app.memory.memory_schema import MemoryRecord
from app.schemas.writer import WriterRequest
from app.schemas.reflection import ReflectionRequest
from app.schemas.planner import PlannerRequest
from app.workflows.state import ResearchState

from app.search.content_extractor import content_extractor
from app.search.document_normalizer import document_normalizer
from app.search.chunker import semantic_chunker
from app.search.embedder import chunk_embedder
from app.search.retriever import semantic_retriever
from app.search.cross_encoder import cross_encoder
from app.intelligence.quality import quality_engine
from app.rewrite.planner import rewrite_planner
from app.rewrite.agent import rewrite_agent
from app.citations.injector import citation_injector

# ─────────────────────────────────────────────────────────────────────────────
# Tuning constants — sourced from Settings (app/core/config.py) so production's
# ~1GB worker container can run a more conservative profile than local dev
# without a code change; see the "Research pipeline resource limits" section
# there for why these exist.
# ─────────────────────────────────────────────────────────────────────────────

# Cap how many sources we download during chunking (performance guard)
MAX_SOURCES_FOR_CHUNKING = settings.MAX_SOURCES_FOR_CHUNKING

# Max parallel threads for URL extraction
EXTRACTION_WORKERS = settings.EXTRACTION_WORKERS

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _start(name: str) -> float:
    logger.info(f"[{name}] start")
    return time.perf_counter()


def _end(name: str, t0: float):
    elapsed = time.perf_counter() - t0
    logger.info(f"[{name}] end", extra={"elapsed_s": round(elapsed, 2)})


def _before(label: str) -> float:
    logger.debug(f"before {label}")
    return time.perf_counter()


def _after(label: str, t0: float):
    elapsed = time.perf_counter() - t0
    logger.debug(f"after {label}", extra={"elapsed_s": round(elapsed, 2)})


def _state_snapshot(state: dict):
    logger.debug(
        "state snapshot",
        extra={
            "query": state.get("query", "")[:60],
            "objective": str(state.get("objective", ""))[:80],
            "tasks": len(state.get("tasks", [])),
            "search_results": len(state.get("search_results", [])),
            "ranked_sources": len(state.get("ranked_sources", [])),
            "chunk_pool": len(state.get("chunk_pool", [])),
            "context_len": len(state.get("context", "")),
            "report_len": len(state.get("report", "")),
            "quality_report": state.get("quality_report") is not None,
            "reflection": state.get("reflection") is not None,
            "iteration": state.get("iteration", 0),
            "max_iterations": state.get("max_iterations", 0),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Planner
# ─────────────────────────────────────────────────────────────────────────────

def planner_node(state: ResearchState) -> ResearchState:

    t_node = _start("Planner Node")
    query = state["query"]
    logger.debug("planner input", extra={"query": query})

    t0 = _before("planner_agent.create_plan()")
    try:
        result = planner_agent.create_plan(
            PlannerRequest(query=query, previous_research="")
        )
    except Exception as e:
        logger.error(f"planner_agent.create_plan() failed: {e}")
        raise
    _after("planner_agent.create_plan()", t0)

    logger.debug(
        "planner output",
        extra={"objective": result.objective[:120], "task_count": len(result.tasks)},
    )

    state["objective"] = result.objective
    state["tasks"] = result.tasks
    state["search_queries"] = result.tasks

    _state_snapshot(state)
    _end("Planner Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 2. Memory Search
# ─────────────────────────────────────────────────────────────────────────────

def memory_search_node(state: ResearchState) -> ResearchState:

    t_node = _start("Memory Search Node")

    if not state.get("memory_enabled", True):
        logger.debug("memory disabled — skipping")
        _end("Memory Search Node", t_node)
        return state

    t0 = _before("memory_manager.retrieve()")
    try:
        results = memory_manager.retrieve(query=state["query"], top_k=3)
    except Exception as e:
        logger.warning(f"memory_manager.retrieve() failed: {e}")
        results = []
    _after("memory_manager.retrieve()", t0)

    state["memory_results"] = results if results is not None else []

    _end("Memory Search Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 3. Search
# ─────────────────────────────────────────────────────────────────────────────

def search_node(state: ResearchState) -> ResearchState:

    t_node = _start("Search Node")
    logger.debug("search input", extra={"objective": state["objective"][:120]})

    t0 = _before("search_agent.generate_queries()")
    try:
        queries = search_agent.generate_queries(state["objective"])
    except Exception as e:
        logger.error(f"generate_queries() failed: {e}")
        raise
    _after("search_agent.generate_queries()", t0)

    logger.debug("generated queries", extra={"count": len(queries)})

    state["search_queries"] = queries

    t0 = _before("search_agent.search()")
    try:
        results = search_agent.search(queries)
    except Exception as e:
        logger.error(f"search_agent.search() failed: {e}")
        raise
    _after("search_agent.search()", t0)

    logger.debug("search results", extra={"count": len(results)})
    state["search_results"] = results

    _state_snapshot(state)
    _end("Search Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 4. Ranking
# ─────────────────────────────────────────────────────────────────────────────

def ranking_node(state: ResearchState) -> ResearchState:

    t_node = _start("Ranking Node")
    logger.debug("ranking input", extra={"sources": len(state["search_results"])})

    t0 = _before("source_ranker.rank()")
    try:
        ranked = source_ranker.rank(state["search_results"])
    except Exception as e:
        logger.error(f"source_ranker.rank() failed: {e}")
        raise
    _after("source_ranker.rank()", t0)

    logger.debug("ranked sources", extra={"count": len(ranked)})

    state["ranked_sources"] = ranked

    _state_snapshot(state)
    _end("Ranking Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 5. Chunking  — PARALLEL extraction, capped at MAX_SOURCES_FOR_CHUNKING
# ─────────────────────────────────────────────────────────────────────────────

def _extract_and_chunk_source(source, idx: int, total: int):
    """
    Worker function run in ThreadPoolExecutor.
    Returns list[SearchChunk] or empty list on failure.
    """
    logger.debug(f"chunking source {idx}/{total}", extra={"url": source.url[:80]})
    t0 = time.perf_counter()

    try:
        text = content_extractor.extract(source.url)
    except Exception as e:
        logger.warning(f"extraction failed for source {idx}: {e}")
        return []

    if not text:
        logger.debug(f"source {idx}: extraction returned empty — skipping")
        return []

    if len(text) > settings.MAX_SOURCE_CONTENT_CHARS:
        logger.debug(
            f"source {idx}: extracted text truncated",
            extra={"original_chars": len(text), "cap": settings.MAX_SOURCE_CONTENT_CHARS},
        )
        text = text[: settings.MAX_SOURCE_CONTENT_CHARS]

    logger.debug(
        f"source {idx}: extracted",
        extra={"chars": len(text), "elapsed_s": round(time.perf_counter() - t0, 2)},
    )

    try:
        text = document_normalizer.normalize(text)
    except Exception as e:
        logger.warning(f"normalization failed for source {idx}: {e}")
        return []

    try:
        chunks = semantic_chunker.chunk(text=text, title=source.title, url=source.url)
    except Exception as e:
        logger.warning(f"chunking failed for source {idx}: {e}")
        return []

    logger.debug(f"source {idx}: chunked", extra={"chunk_count": len(chunks)})

    # Tag source name on each chunk
    for ch in chunks:
        ch.source_name = source.source

    return chunks


def chunking_node(state: ResearchState) -> ResearchState:

    t_node = _start("Chunking Node")
    ranked_sources = state.get("ranked_sources", [])

    # Cap sources to avoid excessively long extraction
    sources_to_process = ranked_sources[:MAX_SOURCES_FOR_CHUNKING]
    logger.debug(
        "chunking scope",
        extra={"available": len(ranked_sources), "to_process": len(sources_to_process), "cap": MAX_SOURCES_FOR_CHUNKING},
    )

    if not sources_to_process:
        logger.debug("no sources — chunk_pool will be empty")
        state["chunk_pool"] = []
        _end("Chunking Node", t_node)
        return state

    # ── Parallel extraction ──────────────────────────────────────────────────
    all_raw_chunks = []
    total = len(sources_to_process)

    t0 = _before(f"parallel extraction ({EXTRACTION_WORKERS} workers)")
    with ThreadPoolExecutor(max_workers=EXTRACTION_WORKERS) as executor:
        futures = {
            executor.submit(_extract_and_chunk_source, src, i + 1, total): src
            for i, src in enumerate(sources_to_process)
        }
        for future in as_completed(futures):
            try:
                chunks = future.result()
                all_raw_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"chunking worker failed: {e}")
    _after("parallel extraction", t0)

    logger.debug("raw chunks collected", extra={"count": len(all_raw_chunks)})

    if not all_raw_chunks:
        logger.warning("no chunks extracted from any source")
        state["chunk_pool"] = []
        _end("Chunking Node", t_node)
        return state

    # ── Embedding (batch, sequential to avoid OOM) ───────────────────────────
    t0 = _before("chunk_embedder.embed() [all chunks]")
    try:
        embedded_chunks = chunk_embedder.embed(all_raw_chunks)
    except Exception as e:
        logger.error(f"embedding chunks failed: {e}")
        embedded_chunks = all_raw_chunks  # keep without embeddings; retriever guards NoneType
    _after("chunk_embedder.embed()", t0)

    state["chunk_pool"] = embedded_chunks
    logger.debug("chunk pool built", extra={"size": len(state["chunk_pool"])})

    _state_snapshot(state)
    _end("Chunking Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 6. Retrieval
# ─────────────────────────────────────────────────────────────────────────────

def retrieval_node(state: ResearchState) -> ResearchState:

    t_node = _start("Retrieval Node")

    chunk_pool = state.get("chunk_pool", [])
    logger.debug("retrieval input", extra={"chunk_pool_size": len(chunk_pool)})

    if not chunk_pool:
        logger.warning("chunk pool is empty — context will be empty")
        state["context"] = ""
        _end("Retrieval Node", t_node)
        return state

    # Build query list: tasks + reflection missing-info
    queries = list(state.get("tasks", []))
    reflection = state.get("reflection")
    if reflection and not reflection.get("approved"):
        for info in reflection.get("missing_information", []):
            if info and info.strip():
                queries.append(f"Missing details on: {info}")

    logger.debug("retrieval queries", extra={"count": len(queries)})

    structured_context = []

    for task_idx, query in enumerate(queries, start=1):
        logger.debug(f"retrieval task {task_idx}/{len(queries)}", extra={"query": query[:80]})

        # Semantic retrieval
        t0 = _before(f"semantic_retriever.retrieve(task {task_idx})")
        try:
            retrieved_chunks = semantic_retriever.retrieve(
                query=query, chunks=chunk_pool, top_k=15,
            )
        except Exception as e:
            logger.warning(f"semantic_retriever.retrieve() failed: {e}")
            retrieved_chunks = []
        _after(f"semantic_retriever.retrieve(task {task_idx})", t0)
        logger.debug(f"task {task_idx}: retrieved", extra={"count": len(retrieved_chunks)})

        if not retrieved_chunks:
            continue

        # Cross-encoder reranking
        t0 = _before(f"cross_encoder.rerank(task {task_idx})")
        try:
            reranked_pairs = cross_encoder.rerank(query=query, chunks=retrieved_chunks)
        except Exception as e:
            logger.warning(f"cross_encoder.rerank() failed: {e}")
            reranked_pairs = [(ch, 0.0) for ch in retrieved_chunks]
        _after(f"cross_encoder.rerank(task {task_idx})", t0)
        logger.debug(f"task {task_idx}: reranked", extra={"count": len(reranked_pairs)})

        # Source deduplication: max 2 per source_url
        deduplicated: list = []
        url_counts: dict[str, int] = {}
        for chunk, score in reranked_pairs:
            url = chunk.source_url.strip().lower()
            if url_counts.get(url, 0) >= 2:
                continue
            url_counts[url] = url_counts.get(url, 0) + 1
            chunk.similarity = float(score)
            deduplicated.append(chunk)

        top_chunks = deduplicated[:3]
        logger.debug(f"task {task_idx}: deduplicated", extra={"top_chunks": len(top_chunks)})

        if not top_chunks:
            continue

        section_md = f"## Section {task_idx}: {query}\n\n"
        for chunk in top_chunks:
            source_name = chunk.source_name or "Web Source"
            section_md += (
                f"Source: {source_name}\n"
                f"URL: {chunk.source_url}\n"
                f"Title: {chunk.source_title}\n"
                f"Snippet:\n{chunk.text}\n\n"
            )
        section_md += "-------------------\n\n"
        structured_context.append(section_md)

    state["context"] = "".join(structured_context)
    logger.debug("context built", extra={"chars": len(state["context"])})

    _state_snapshot(state)
    _end("Retrieval Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 7. Writer
# ─────────────────────────────────────────────────────────────────────────────

def writer_node(state: ResearchState) -> ResearchState:

    t_node = _start("Writer Node")

    context = state.get("context", "")
    tasks = state.get("tasks", [])
    sources = state.get("ranked_sources", [])

    logger.debug(
        "writer input",
        extra={"context_len": len(context), "tasks": len(tasks), "sources": len(sources)},
    )

    request = WriterRequest(
        objective=state["objective"],
        tasks=tasks,
        sources=sources,
        context=context,
    )

    t0 = _before("writer_agent.generate_report()")
    try:
        response = writer_agent.generate_report(request)
    except Exception as e:
        logger.error(f"writer_agent.generate_report() failed: {e}")
        raise
    _after("writer_agent.generate_report()", t0)

    state["report"] = response.report
    logger.debug("report generated", extra={"chars": len(state["report"])})

    # Store in memory (non-fatal if it fails)
    t0 = _before("memory_manager.store()")
    try:
        memory_manager.store(
            MemoryRecord(
                id=str(uuid4()),
                query=state["query"],
                objective=state["objective"],
                report=state["report"],
                created_at=datetime.now(),
            )
        )
    except Exception as e:
        logger.warning(f"memory_manager.store() failed (non-fatal): {e}")
    _after("memory_manager.store()", t0)

    _state_snapshot(state)
    _end("Writer Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 8. Verification
# ─────────────────────────────────────────────────────────────────────────────

def verification_node(state: ResearchState) -> ResearchState:

    t_node = _start("Verification Node")

    report = state.get("report", "")
    sources = state.get("ranked_sources", [])
    chunk_pool = state.get("chunk_pool", [])

    paragraphs = [p.strip() for p in report.split("\n\n") if p.strip()]
    logger.debug(
        "verification input",
        extra={"paragraphs": len(paragraphs), "chunk_pool_size": len(chunk_pool), "sources": len(sources)},
    )

    t0 = _before("quality_engine.evaluate()")
    try:
        quality_report = quality_engine.evaluate(
            report=report,
            sources=sources,
            chunk_pool=chunk_pool,          # fast path: no re-downloads
        )
    except Exception as e:
        logger.error(f"quality_engine.evaluate() failed: {e}")
        raise
    _after("quality_engine.evaluate()", t0)

    state["quality_report"] = quality_report

    logger.info(
        "verification completed",
        extra={
            "overall_score": quality_report.overall_score,
            "supported_paragraphs": quality_report.supported_paragraphs,
            "total_paragraphs": quality_report.total_paragraphs,
            "hallucinated_paragraphs": quality_report.hallucinated_paragraphs,
        },
    )

    _state_snapshot(state)
    _end("Verification Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 9. Rewrite
# ─────────────────────────────────────────────────────────────────────────────

def rewrite_node(state: ResearchState) -> ResearchState:

    t_node = _start("Rewrite Node")

    quality_report = state.get("quality_report")
    if not quality_report:
        logger.warning("no quality_report — skipping rewrite")
        _end("Rewrite Node", t_node)
        return state

    t0 = _before("rewrite_planner.create_plan()")
    try:
        tasks = rewrite_planner.create_plan(quality_report)
    except Exception as e:
        logger.error(f"rewrite_planner.create_plan() failed: {e}")
        raise
    _after("rewrite_planner.create_plan()", t0)

    logger.debug("rewrite tasks", extra={"count": len(tasks)})

    if not tasks:
        logger.debug("no paragraphs need rewriting")
        _end("Rewrite Node", t_node)
        return state

    paragraphs = [
        p.strip()
        for p in state["report"].split("\n\n")
        if p.strip()
    ]
    logger.debug("paragraphs in report", extra={"count": len(paragraphs)})

    for i, task in enumerate(tasks, 1):
        logger.debug(
            f"rewrite {i}/{len(tasks)}",
            extra={"paragraph_index": task.paragraph_index, "strategy": task.rewrite_strategy.value},
        )

        t0 = _before(f"rewrite_agent.rewrite(task {i})")
        try:
            response = rewrite_agent.rewrite(task)
        except Exception as e:
            logger.warning(f"rewrite_agent.rewrite() failed: {e} — keeping original")
            continue
        _after(f"rewrite_agent.rewrite(task {i})", t0)

        idx = response.paragraph_index
        if 0 <= idx < len(paragraphs):
            paragraphs[idx] = response.rewritten_paragraph
            logger.debug(f"replaced paragraph {idx}", extra={"chars": len(response.rewritten_paragraph)})
        else:
            logger.warning(f"paragraph_index {idx} out of range ({len(paragraphs)}) — skipping")

    state["report"] = "\n\n".join(paragraphs)
    logger.debug("report length after rewrite", extra={"chars": len(state["report"])})

    _state_snapshot(state)
    _end("Rewrite Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 10. Citation
# ─────────────────────────────────────────────────────────────────────────────

def citation_node(state: ResearchState) -> ResearchState:

    t_node = _start("Citation Node")

    report = state["report"]
    sources = state["ranked_sources"]
    chunk_pool = state.get("chunk_pool", [])

    logger.debug(
        "citation input",
        extra={"report_len": len(report), "sources": len(sources), "chunk_pool_size": len(chunk_pool)},
    )

    t0 = _before("citation_injector.inject()")
    try:
        injected_report = citation_injector.inject(
            report=report,
            sources=sources,
            chunk_pool=chunk_pool,          # fast path: no re-downloads
        )
    except Exception as e:
        logger.error(f"citation_injector.inject() failed: {e}")
        raise
    _after("citation_injector.inject()", t0)

    state["report"] = injected_report
    logger.debug("citation injected", extra={"report_len": len(injected_report)})

    _state_snapshot(state)
    _end("Citation Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 11. Reflection
# ─────────────────────────────────────────────────────────────────────────────

def reflection_node(state: ResearchState) -> ResearchState:

    t_node = _start("Reflection Node")

    logger.debug("reflection input", extra={"report_len": len(state["report"])})

    request = ReflectionRequest(
        objective=state["objective"],
        report=state["report"],
    )

    t0 = _before("reflection_agent.review()")
    try:
        response = reflection_agent.review(request)
    except Exception as e:
        logger.error(f"reflection_agent.review() failed: {e} — fail-safe approving to prevent infinite loop")
        from app.schemas.reflection import ReflectionResponse
        response = ReflectionResponse(
            approved=True,
            feedback=f"Review failed due to error: {e}",
            missing_information=[],
        )
    _after("reflection_agent.review()", t0)

    state["reflection"] = response.model_dump()
    state["iteration"] += 1

    logger.info(
        "reflection completed",
        extra={
            "approved": response.approved,
            "iteration": state["iteration"],
            "max_iterations": state["max_iterations"],
        },
    )

    _state_snapshot(state)
    _end("Reflection Node", t_node)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 12. Routing
# ─────────────────────────────────────────────────────────────────────────────

def should_continue(state: ResearchState) -> str:

    reflection = state["reflection"]
    iteration = state["iteration"]
    max_iter = state["max_iterations"]

    approved = reflection["approved"]

    if approved:
        logger.info("research approved", extra={"iteration": iteration, "max_iterations": max_iter})
        return "approve"

    if iteration >= max_iter:
        logger.warning("max iterations reached — forcing approval", extra={"iteration": iteration, "max_iterations": max_iter})
        return "approve"

    logger.info("reflection requested another research iteration", extra={"iteration": iteration, "max_iterations": max_iter})
    return "research_more"
