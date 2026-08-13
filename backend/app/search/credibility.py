from app.search.schemas import SearchResult


DOMAIN_SCORES = {
    "nature.com": 100,
    "science.org": 100,
    "arxiv.org": 95,
    "openai.com": 95,
    "anthropic.com": 95,
    "langchain.com": 95,
    "python.org": 90,
    "docs.python.org": 90,
    "ibm.com": 90,
    "microsoft.com": 90,
    "aws.amazon.com": 90,
    "cloud.google.com": 90,
    "github.com": 85,
    "pypi.org": 85,
    "wikipedia.org": 75,
    "medium.com": 55,
}


class CredibilityScorer:

    def score(
        self,
        result: SearchResult,
    ) -> int:

        return DOMAIN_SCORES.get(
            result.domain,
            40,
        )


credibility_scorer = CredibilityScorer()