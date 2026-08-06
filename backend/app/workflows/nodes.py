from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker
from app.agents.writer_agent import writer_agent
from app.agents.reflection_agent import reflection_agent

from app.core.logger import logger
from app.memory.manager import memory_manager
from app.memory.memory_schema import MemoryRecord
from app.schemas.writer import WriterRequest
from app.schemas.reflection import ReflectionRequest
from app.schemas.planner import PlannerRequest
from app.workflows.state import ResearchState

from datetime import datetime
from uuid import uuid4

def planner_node(state: ResearchState):

    logger.info("Planner Agent Started")

    previous_research = ""

    memory_results = state.get("memory_results")

    if memory_results:

        documents = memory_results.get("documents", [])

        if documents and documents[0]:

            previous_research = "\n\n".join(
                documents[0]
            )

    request = PlannerRequest(
        query=state["query"],
        previous_research=previous_research,
    )

    response = planner_agent.create_plan(
        request
    )

    state["objective"] = response.objective
    state["tasks"] = response.tasks

    logger.info("Planner Agent Completed")

    return state

def memory_search_node(state: ResearchState):

    logger.info("Memory Search Started")

    if not state.get("memory_enabled", True):

        logger.info("Memory Disabled")

        return state

    results = memory_manager.retrieve(
        query=state["query"],
        top_k=3,
    )

    state["memory_results"] = results

    logger.info("Memory Search Completed")

    return state


def search_node(state: ResearchState):

    logger.info("Search Agent Started")

    queries = search_agent.generate_queries(
        state["objective"]
    )

    logger.info(f"Generated {len(queries)} search queries")

    state["search_queries"] = queries

    results = search_agent.search(queries)

    state["search_results"] = results

    logger.info(f"Collected {len(results)} search results")
    logger.info("Search Agent Completed")

    return state


def ranking_node(state: ResearchState):

    logger.info("Ranking Agent Started")

    ranked = source_ranker.rank(
        state["search_results"]
    )

    state["ranked_sources"] = ranked

    logger.info(
        f"Ranked {len(ranked)} high-quality sources"
    )

    logger.info("Ranking Agent Completed")

    return state


def writer_node(state: ResearchState):

    logger.info("Writer Agent Started")

    request = WriterRequest(
        objective=state["objective"],
        tasks=state["tasks"],
        sources=state["ranked_sources"],
    )

    response = writer_agent.generate_report(
        request
    )

    state["report"] = response.report

    # -----------------------------
    # Store report in memory
    # -----------------------------
    memory_manager.store(
        MemoryRecord(
            id=str(uuid4()),
            query=state["query"],
            objective=state["objective"],
            report=state["report"],
            created_at=datetime.now(),
        )
    )

    logger.info("Research stored in memory")

    logger.info("Writer Agent Completed")

    return state


def reflection_node(state: ResearchState):

    logger.info("Reflection Agent Started")

    request = ReflectionRequest(
        objective=state["objective"],
        report=state["report"],
    )

    response = reflection_agent.review(
        request
    )

    state["reflection"] = response.model_dump()

    state["iteration"] += 1

    logger.info("Reflection Agent Completed")

    return state


def should_continue(state: ResearchState):

    reflection = state["reflection"]

    if reflection["approved"]:
        logger.info("Research Approved")
        return "approve"

    if state["iteration"] >= state["max_iterations"]:
        logger.warning(
            "Maximum iterations reached. Approving current report."
        )
        return "approve"

    logger.info("Reflection requested another research iteration")

    return "research_more"

def memory_search_node(state: ResearchState):

    logger.info("Memory Search Started")

    if not state.get("memory_enabled", True):
        logger.info("Memory disabled.")
        return state

    results = memory_manager.retrieve(
        query=state["query"],
        top_k=3,
    )

    state["memory_results"] = results

    logger.info("Memory Search Completed")

    return state