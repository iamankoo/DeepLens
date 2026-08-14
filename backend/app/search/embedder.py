import time

from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)
from app.search.chunk import SearchChunk


class ChunkEmbedder:
    """
    Embeds all chunks in a SINGLE batch model.encode() call.
    """

    def embed(
        self,
        chunks: list[SearchChunk],
    ) -> list[SearchChunk]:

        if not chunks:
            return chunks

        total = len(chunks)
        print(f"    [ChunkEmbedder] Batch-embedding {total} chunks...")
        t0 = time.perf_counter()

        texts = [chunk.text for chunk in chunks]

        try:
            embeddings = sentence_transformer_provider.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=64,
            )
            for chunk, emb in zip(chunks, embeddings):
                chunk.embedding = emb.tolist()
        except Exception as e:
            print(f"    [ChunkEmbedder] Batch embed ERROR: {e} — falling back to per-chunk")
            for i, chunk in enumerate(chunks, 1):
                try:
                    chunk.embedding = sentence_transformer_provider.embed(chunk.text)
                except Exception as e2:
                    print(f"    [ChunkEmbedder] ERROR chunk {i}: {e2}")
                    chunk.embedding = [0.0] * 384

        elapsed = time.perf_counter() - t0
        print(f"    [ChunkEmbedder] Done — {total} chunks in {elapsed:.2f}s")
        return chunks


chunk_embedder = ChunkEmbedder()