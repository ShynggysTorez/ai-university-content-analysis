"""University Content Intelligence."""

from .analytics import (
    calculate_label_counts,
    summary_statistics,
    top_categories,
)
from .classifier import ClassificationResult, ContentClassifier
from .config import ClassificationConfig
from .llm_client import (
    LLMRequestError,
    MissingAPIKeyError,
    OpenAIClient,
)
from .taxonomy import DEFAULT_CATEGORIES

__all__ = [
    "ClassificationConfig",
    "ClassificationResult",
    "ContentClassifier",
    "DEFAULT_CATEGORIES",
    "LLMRequestError",
    "MissingAPIKeyError",
    "OpenAIClient",
    "calculate_label_counts",
    "summary_statistics",
    "top_categories",
]

__version__ = "1.0.0"
