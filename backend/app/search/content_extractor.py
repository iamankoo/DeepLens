import time

import requests
import trafilatura


class ContentExtractor:

    # Hard timeout: if a page doesn't respond in this many seconds, skip it.
    FETCH_TIMEOUT = 10

    def extract(
        self,
        url: str,
    ) -> str | None:

        print(f"    [ContentExtractor] Fetching: {url}")
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
            print(f"    [ContentExtractor] TIMEOUT after {elapsed:.1f}s — skipping {url}")
            return None
        except requests.exceptions.RequestException as e:
            elapsed = time.perf_counter() - t0
            print(f"    [ContentExtractor] REQUEST ERROR after {elapsed:.1f}s: {e}")
            return None
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"    [ContentExtractor] UNEXPECTED ERROR after {elapsed:.1f}s: {e}")
            return None

        elapsed_fetch = time.perf_counter() - t0
        print(f"    [ContentExtractor] Fetched {len(raw_html)} chars in {elapsed_fetch:.2f}s")

        t1 = time.perf_counter()
        try:
            text = trafilatura.extract(
                raw_html,
                include_comments=False,
                include_tables=False,
                include_links=False,
            )
        except Exception as e:
            print(f"    [ContentExtractor] trafilatura.extract ERROR: {e}")
            return None

        elapsed_parse = time.perf_counter() - t1
        if text:
            print(f"    [ContentExtractor] Extracted {len(text)} chars in {elapsed_parse:.2f}s")
        else:
            print(f"    [ContentExtractor] trafilatura returned None in {elapsed_parse:.2f}s — skipping")

        return text


content_extractor = ContentExtractor()