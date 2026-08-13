from pydantic import BaseModel


from app.intelligence.schemas import EvidenceResult

class QualityReport(BaseModel):

    total_paragraphs: int

    supported_paragraphs: int

    hallucinated_paragraphs: int

    evidence_score: float

    hallucination_score: float

    overall_score: float

    evidence_results: list[EvidenceResult]