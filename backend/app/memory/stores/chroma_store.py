import chromadb

from app.core.config import settings
from app.core.logger import logger
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
            logger.debug("ChromaStore initialized", extra={"path": settings.CHROMA_PERSIST_DIRECTORY})
        except Exception as e:
            logger.error("ChromaStore failed to initialize — long-term memory disabled", extra={"error": str(e)})
            self.client = None
            self.collection = None

    def add_memory(self, memory: MemoryRecord):
        if self.collection is None:
            logger.warning("no ChromaStore collection — skipping memory store", extra={"memory_id": memory.id})
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
            logger.debug("memory stored", extra={"memory_id": memory.id})
        except Exception as e:
            logger.warning("failed to store memory", extra={"memory_id": memory.id, "error": str(e)})

    def search(self, query: str, top_k: int = 5):
        if self.collection is None:
            logger.warning("no ChromaStore collection — returning empty memory search")
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
            logger.warning("memory search failed", extra={"error": str(e)})
            return {"ids": [], "documents": [], "metadatas": []}


chroma_store = ChromaStore()
