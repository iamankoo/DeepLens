from app.workflows.research_workflow import research_graph


initial_state = {
    "query": "Research LangGraph",

    "objective": "",
    "tasks": [],

    "search_queries": [],
    "search_results": [],
    "ranked_sources": [],

    "report": "",

    "reflection": None,

    "iteration": 0,
    "max_iterations": 3,
}


result = research_graph.invoke(initial_state)

print("\n" + "=" * 80)
print("FINAL REPORT")
print("=" * 80)
print(result["report"])

print("\n" + "=" * 80)
print("REFLECTION")
print("=" * 80)
print(result["reflection"])

print("\n" + "=" * 80)
print("ITERATIONS")
print("=" * 80)
print(result["iteration"])