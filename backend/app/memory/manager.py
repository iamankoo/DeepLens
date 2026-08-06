from app.memory.memory_schema import MemoryRecord
from app.memory.stores.chroma_store import chroma_store


class MemoryManager:

    def store(
        self,
        memory: MemoryRecord,
    ) -> None:
        """
        Store a research memory.
        """

        chroma_store.add_memory(memory)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ):
        """
        Retrieve similar research memories.
        """

        return chroma_store.search(
            query=query,
            top_k=top_k,
        )


memory_manager = MemoryManager()