from uuid import uuid4
from datetime import datetime

from app.memory.memory_schema import MemoryRecord
from app.memory.stores.chroma_store import chroma_store


memory = MemoryRecord(
    id=str(uuid4()),
    query="Research LangGraph",
    objective="Understand LangGraph",
    report="""
LangGraph is a framework for building stateful AI agents.
It supports cycles, memory, and tool calling.
""",
    created_at=datetime.now(),
)

chroma_store.add_memory(memory)

results = chroma_store.search(
    "LangGraph memory"
)

print(results)