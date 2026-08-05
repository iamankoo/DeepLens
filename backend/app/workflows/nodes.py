from app.agents.planner_agent import planner_agent
from app.agents.search_agent import search_agent
from app.agents.source_ranker import source_ranker
from app.agents.writer_agent import writer_agent
from app.core.logger import logger
from app.workflows.state import ResearchState


def planner_node(state: ResearchState):

    logger.info("Planner Agent Started")

    plan = planner_agent.create_plan(state["query"])

    state["objective"] = plan["objective"]
    state["tasks"] = plan["tasks"]

    logger.info("Planner Agent Completed")

    return state


def search_node(state: ResearchState):

    logger.info("Search Agent Started")

    queries = search_agent.generate_queries(state["objective"])

    logger.info(f"Generated {len(queries)} search queries")

    state["search_queries"] = queries

    results = search_agent.search(queries)

    state["search_results"] = results

    logger.info(f"Collected {len(results)} search results")
    logger.info("Search Agent Completed")

    return state


def ranking_node(state: ResearchState):

    logger.info("Ranking Agent Started")

    ranked = source_ranker.rank(state["search_results"])

    state["ranked_sources"] = ranked

    logger.info(f"Ranked {len(ranked)} high-quality sources")
    logger.info("Ranking Agent Completed")

    return state


def writer_node(state: ResearchState):

    logger.info("Writer Agent Started")

    report = writer_agent.generate_report(state)

    state["report"] = report

    logger.info("Writer Agent Completed")

    return state