from app.agents.reflection_agent import reflection_agent
from app.schemas.reflection import ReflectionRequest


def test_reflection():

    print("Testing Reflection Agent...")

    request = ReflectionRequest(
        objective="Analyze LangGraph orchestrator",
        report="LangGraph is an orchestration framework designed to build stateful AI agent workflows. It supports cyclic architectures and persistent state management."
    )

    response = reflection_agent.review(request)

    assert response.approved is not None, "Approved field is None"

    assert response.feedback != "", "Feedback is empty"

    print("Reflection Agent works successfully.")


if __name__ == "__main__":

    test_reflection()
