from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker
from app.agents.writer_agent import writer_agent
from app.agents.reflection_agent import reflection_agent

from app.core.logger import logger

from app.schemas.writer import WriterRequest
from app.schemas.reflection import ReflectionRequest

from app.workflows.state import ResearchState


def planner_node(state: ResearchState):

    logger.info("Planner Agent Started")

    plan = planner_agent.create_plan(state["query"])

    state["objective"] = plan.objective
    state["tasks"] = plan.tasks

    logger.info("Planner Agent Completed")

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