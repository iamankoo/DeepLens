class PlannerAgent:

    def create_plan(self, query: str):

        query_lower = query.lower()

        if "compare" in query_lower:
            tasks = [
                "Research first topic",
                "Research second topic",
                "Compare both topics",
                "Generate comparison report",
            ]

        elif "explain" in query_lower:
            tasks = [
                "Research the topic",
                "Understand the architecture",
                "Analyze key concepts",
                "Generate explanation report",
            ]

        else:
            tasks = [
                "Understand the topic",
                "Collect information",
                "Analyze findings",
                "Generate report",
            ]

        return {
            "objective": query,
            "tasks": tasks,
        }


planner_agent = PlannerAgent()
