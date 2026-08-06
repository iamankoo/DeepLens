import chromadb

from app.memory.memory_schema import MemoryRecord
from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)


class ChromaStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="research_memory"
        )

    def add_memory(
        self,
        memory: MemoryRecord,
    ):

        embedding = sentence_transformer_provider.embed(
            memory.report
        )

        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            documents=[memory.report],
            metadatas=[
                {
                    "query": memory.query,
                    "objective": memory.objective,
                }
            ],
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):

        embedding = sentence_transformer_provider.embed(
            query
        )

        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )


chroma_store = ChromaStore()