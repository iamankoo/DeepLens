from datetime import datetime
from uuid import uuid4

from app.memory.manager import memory_manager
from app.memory.memory_schema import MemoryRecord


memory = MemoryRecord(
    id=str(uuid4()),
    query="Research CrewAI",
    objective="Understand CrewAI",
    report="""
CrewAI is a framework for building collaborative AI agents.
It focuses on role-based autonomous agents.
""",
    created_at=datetime.now(),
)

memory_manager.store(memory)

results = memory_manager.retrieve(
    "AI agent framework"
)

print(results)