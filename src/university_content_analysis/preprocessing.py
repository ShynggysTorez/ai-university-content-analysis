"""Text preprocessing utilities."""

from __future__ import annotations

import math
import re
from typing import Any


def normalize_text(value: Any) -> str:
    """Convert a value to clean text and normalize whitespace."""

    if value is None:
        return ""

    if isinstance(value, float) and math.isnan(value):
        return ""

    text = str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def truncate_text(text: str, max_chars: int = 12_000) -> str:
    """Limit text to a maximum number of characters."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    return text[:max_chars]


def build_document(
    title: Any,
    url: Any,
    content: Any,
    max_chars: int = 12_000,
) -> str:
    """Combine page metadata and content into one classification document."""

    clean_title = normalize_text(title)
    clean_url = normalize_text(url)
    clean_content = truncate_text(normalize_text(content), max_chars)

    return (
        f"Title: {clean_title}\n\nURL: {clean_url}\n\nContent:\n{clean_content}"
    ).strip()
