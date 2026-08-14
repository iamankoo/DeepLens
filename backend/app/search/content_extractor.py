import time

import requests
import trafilatura

from app.core.logger import logger


class ContentExtractor:

    # Hard timeout: if a page doesn't respond in this many seconds, skip it.
    FETCH_TIMEOUT = 10

    def extract(
        self,
        url: str,
    ) -> str | None:

        logger.debug("fetching url", extra={"url": url})
        t0 = time.perf_counter()

        try:
            response = requests.get(
                url,
                timeout=self.FETCH_TIMEOUT,
                headers={"User-Agent": "DeepLens-Research-Bot/1.0"},
            )
            response.raise_for_status()
            raw_html = response.text
        except requests.exceptions.Timeout:
            elapsed = time.perf_counter() - t0
            logger.warning("fetch timed out — skipping", extra={"url": url, "elapsed_s": round(elapsed, 1)})
            return None
        except requests.exceptions.RequestException as e:
            elapsed = time.perf_counter() - t0
            logger.warning("request error", extra={"url": url, "elapsed_s": round(elapsed, 1), "error": str(e)})
            return None
        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error("unexpected error fetching url", extra={"url": url, "elapsed_s": round(elapsed, 1), "error": str(e)})
            return None

        elapsed_fetch = time.perf_counter() - t0
        logger.debug("fetched url", extra={"chars": len(raw_html), "elapsed_s": round(elapsed_fetch, 2)})

        t1 = time.perf_counter()
        try:
            text = trafilatura.extract(
                raw_html,
                include_comments=False,
                include_tables=False,
                include_links=False,
            )
        except Exception as e:
            logger.error("trafilatura.extract error", extra={"error": str(e)})
            return None

        elapsed_parse = time.perf_counter() - t1
        if text:
            logger.debug("extracted text", extra={"chars": len(text), "elapsed_s": round(elapsed_parse, 2)})
        else:
            logger.warning("trafilatura returned None — skipping", extra={"elapsed_s": round(elapsed_parse, 2)})

        return text


content_extractor = ContentExtractor()