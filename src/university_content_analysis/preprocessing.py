"""
Text preprocessing utilities.

This module contains reusable functions for preparing raw text before it is
sent to an LLM or analytical pipeline.
"""

from __future__ import annotations

import re


def normalize_text(text: str | None) -> str:
    """
    Normalize whitespace and safely handle missing values.

    Parameters
    ----------
    text
        Input text.

    Returns
    -------
    str
        Cleaned text.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def truncate_text(
    text: str,
    max_chars: int = 12000,
) -> str:
    """
    Truncate text to the specified maximum number of characters.
    """

    if len(text) <= max_chars:
        return text

    return text[:max_chars]


def build_document(
    title: str | None,
    url: str | None,
    content: str | None,
    max_chars: int = 12000,
) -> str:
    """
    Build a formatted document that will be passed to the LLM.
    """

    title = normalize_text(title)
    url = normalize_text(url)
    content = truncate_text(
        normalize_text(content),
        max_chars=max_chars,
    )

    return f"""Title: {title}

URL: {url}

Content:
{content}
""".strip()