import chromadb

from app.core.config import settings
from app.memory.memory_schema import MemoryRecord
from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)


class ChromaStore:

    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
            self.collection = self.client.get_or_create_collection(
                name="research_memory"
            )
            print("[ChromaStore] Initialized successfully")
        except Exception as e:
            print(f"[ChromaStore] WARNING: Failed to initialize: {e}")
            self.client = None
            self.collection = None

    def add_memory(self, memory: MemoryRecord):
        if self.collection is None:
            print("[ChromaStore] WARNING: No collection — skipping memory store")
            return
        try:
            embedding = sentence_transformer_provider.embed(memory.report[:2000])
            self.collection.add(
                ids=[memory.id],
                embeddings=[embedding],
                documents=[memory.report[:2000]],
                metadatas=[
                    {
                        "query": memory.query[:500],
                        "objective": memory.objective[:500],
                    }
                ],
            )
            print(f"[ChromaStore] Memory stored: id={memory.id[:8]}")
        except Exception as e:
            print(f"[ChromaStore] WARNING: Failed to store memory: {e}")

    def search(self, query: str, top_k: int = 5):
        if self.collection is None:
            print("[ChromaStore] WARNING: No collection — returning empty memory")
            return {"ids": [], "documents": [], "metadatas": []}
        try:
            # Guard against querying an empty collection
            count = self.collection.count()
            if count == 0:
                return {"ids": [], "documents": [], "metadatas": []}
            n = min(top_k, count)
            embedding = sentence_transformer_provider.embed(query)
            return self.collection.query(
                query_embeddings=[embedding],
                n_results=n,
            )
        except Exception as e:
            print(f"[ChromaStore] WARNING: Search failed: {e}")
            return {"ids": [], "documents": [], "metadatas": []}


chroma_store = ChromaStore()