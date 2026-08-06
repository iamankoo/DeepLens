from sentence_transformers import SentenceTransformer

from app.memory.embedding_provider import BaseEmbeddingProvider


class SentenceTransformerProvider(BaseEmbeddingProvider):

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def provider_name(self) -> str:

        return "SentenceTransformers"

    def embed(
        self,
        text: str,
    ) -> list[float]:

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()


sentence_transformer_provider = (
    SentenceTransformerProvider()
)