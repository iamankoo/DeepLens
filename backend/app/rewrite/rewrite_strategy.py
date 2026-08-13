from enum import Enum


class RewriteStrategy(str, Enum):

    KEEP = "keep"

    IMPROVE = "improve"

    REWRITE = "rewrite"

    REMOVE = "remove"