from enum import Enum


class EvidenceLevel(str, Enum):

    STRONG = "strong"

    MODERATE = "moderate"

    WEAK = "weak"

    NONE = "none"