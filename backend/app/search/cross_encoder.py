import time

from sentence_transformers import CrossEncoder


class CrossEncoderRanker:

    def __init__(self):
        print("[CrossEncoder] Loading model: cross-encoder/ms-marco-MiniLM-L-6-v2")
        t0 = time.perf_counter()
        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        elapsed = time.perf_counter() - t0
        print(f"[CrossEncoder] Model loaded in {elapsed:.2f}s")

    def rerank(
        self,
        query,
        chunks,
    ):
        if not chunks:
            return []

        print(f"    [CrossEncoder] Reranking {len(chunks)} chunks...")
        t0 = time.perf_counter()

        try:
            pairs = [
                (query, chunk.text)
                for chunk in chunks
            ]

            scores = self.model.predict(pairs)

        except Exception as e:
            print(f"    [CrossEncoder] ERROR during predict: {e}")
            # Fallback: return chunks with score 0.0
            return [(chunk, 0.0) for chunk in chunks]

        ranked = list(zip(chunks, scores))

        ranked.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        elapsed = time.perf_counter() - t0
        print(f"    [CrossEncoder] Reranked {len(chunks)} chunks in {elapsed:.2f}s")

        return ranked


cross_encoder = CrossEncoderRanker()