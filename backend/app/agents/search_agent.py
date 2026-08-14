import time
from urllib.parse import urlparse

from app.core.logger import logger
from app.providers.search.manager import search_manager
from app.search.schemas import SearchResult
from app.search.credibility import credibility_scorer

from app.memory.providers.sentence_transformer_provider import (
    sentence_transformer_provider,
)


class SearchAgent:

    def generate_queries(self, objective: str) -> list[str]:
        """Generate diverse search queries from the research objective."""
        queries = list(
            dict.fromkeys(
                [
                    objective,
                    f"{objective} overview and examples",
                    f"{objective} best practices and documentation",
                ]
            )
        )
        return queries

    def search(self, queries: list[str]) -> list[SearchResult]:
        """Search all queries, deduplicate, score credibility, embed."""
        all_results: list[SearchResult] = []
        seen_urls: set[str] = set()

        logger.debug("searching queries via provider", extra={"query_count": len(queries)})
        t0 = time.perf_counter()

        for qi, query in enumerate(queries, 1):
            logger.debug("running query", extra={"index": qi, "total": len(queries), "query": query[:80]})
            t1 = time.perf_counter()
            try:
                results = search_manager.search(query)
            except Exception as e:
                logger.error("error searching query", extra={"index": qi, "error": str(e)})
                continue
            elapsed = time.perf_counter() - t1
            logger.debug("query completed", extra={"index": qi, "result_count": len(results), "elapsed_s": round(elapsed, 2)})

            for result in results:
                url = result["url"].strip().lower()
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                domain = urlparse(url).netloc.replace("www.", "")
                source = domain.split(".")[0].capitalize()

                search_result = SearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("snippet", ""),
                    source=source,
                    domain=domain,
                )

                search_result.credibility_score = credibility_scorer.score(search_result)

                # Embed result snippet for later ranking
                embedding_text = (
                    f"Title: {search_result.title}\n"
                    f"Source: {search_result.source}\n"
                    f"Content: {search_result.snippet}"
                )
                try:
                    search_result.embedding = sentence_transformer_provider.embed(
                        embedding_text
                    )
                except Exception as e:
                    logger.warning("embed failed for result", extra={"error": str(e)})
                    search_result.embedding = None

                all_results.append(search_result)

        elapsed_total = time.perf_counter() - t0
        logger.debug(
            "search agent done",
            extra={"unique_results": len(all_results), "elapsed_s": round(elapsed_total, 2)},
        )
        return all_results


search_agent = SearchAgent()