class WriterAgent:

    def generate_report(self, state):

        report = {
            "title": state["objective"],
            "executive_summary": f"DeepLens researched '{state['objective']}' using "
            f"{len(state['ranked_sources'])} trusted sources.",
            "objectives": [state["objective"]],
            "tasks": state["tasks"],
            "sources": state["ranked_sources"],
        }

        return report


writer_agent = WriterAgent()
